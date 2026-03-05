import os
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
import traceback

# Configuration
xml_folder = r"c:\Users\azureuser\Documents\2025_TEOS_XML_01A"
output_excel = r"c:\Users\azureuser\Documents\2025_TEOS_XML_01A\foundations_data.xlsx"
max_files = 20

# Namespace
ns = {'': 'http://www.irs.gov/efile'}

# Data storage
foundations = []
preparers = []
officers = []
financials = []
contributors = []
activities = []
other_expenses = []
professional_fees = []

def safe_text(element, xpath):
    """Safely extract text from XML element"""
    try:
        found = element.find(xpath, ns)
        return found.text if found is not None else ""
    except:
        return ""

def parse_xml(xml_path, foundation_id):
    """Parse single XML file"""
    try:
        xml_filename = Path(xml_path).name
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # ReturnHeader
        header = root.find('{http://www.irs.gov/efile}ReturnHeader')
        if header is None:
            return False
            
        # Filer info
        filer = header.find('{http://www.irs.gov/efile}Filer')
        prep_firm = header.find('{http://www.irs.gov/efile}PreparerFirmGrp')
        prep_person = header.find('{http://www.irs.gov/efile}PreparerPersonGrp')
        officer = header.find('{http://www.irs.gov/efile}BusinessOfficerGrp')
        
        if filer is None:
            return False
        
        # Extract foundation info
        ein = safe_text(filer, '{http://www.irs.gov/efile}EIN')
        org_name = safe_text(filer, '{http://www.irs.gov/efile}BusinessName/{http://www.irs.gov/efile}BusinessNameLine1Txt')
        phone = safe_text(filer, '{http://www.irs.gov/efile}PhoneNum')
        tax_year = safe_text(header, '{http://www.irs.gov/efile}TaxYr')
        tax_period_end = safe_text(header, '{http://www.irs.gov/efile}TaxPeriodEndDt')
        return_type = safe_text(header, '{http://www.irs.gov/efile}ReturnTypeCd')
        
        # Address
        address_elem = filer.find('{http://www.irs.gov/efile}USAddress')
        address_line1 = safe_text(address_elem, '{http://www.irs.gov/efile}AddressLine1Txt') if address_elem else ""
        city = safe_text(address_elem, '{http://www.irs.gov/efile}CityNm') if address_elem else ""
        state = safe_text(address_elem, '{http://www.irs.gov/efile}StateAbbreviationCd') if address_elem else ""
        zip_code = safe_text(address_elem, '{http://www.irs.gov/efile}ZIPCd') if address_elem else ""
        
        # Books location
        books_elem = root.find('.//{http://www.irs.gov/efile}BooksInCareOfDetail')
        books_name = safe_text(books_elem, '{http://www.irs.gov/efile}PersonNm') if books_elem else ""
        books_phone = safe_text(books_elem, '{http://www.irs.gov/efile}PhoneNum') if books_elem else ""
        books_addr = books_elem.find('{http://www.irs.gov/efile}USAddress') if books_elem else None
        books_addr_line1 = safe_text(books_addr, '{http://www.irs.gov/efile}AddressLine1Txt') if books_addr else ""
        books_city = safe_text(books_addr, '{http://www.irs.gov/efile}CityNm') if books_addr else ""
        books_state = safe_text(books_addr, '{http://www.irs.gov/efile}StateAbbreviationCd') if books_addr else ""
        books_zip = safe_text(books_addr, '{http://www.irs.gov/efile}ZIPCd') if books_addr else ""
        
        # Foundation record
        foundations.append({
            'foundation_id': foundation_id,
            'source_xml_file': xml_filename,
            'ein': ein,
            'organization_name': org_name,
            'tax_year': tax_year,
            'tax_period_end_date': tax_period_end,
            'return_type_code': return_type,
            'phone': phone,
            'address_line1': address_line1,
            'city': city,
            'state': state,
            'zip': zip_code,
            'books_location_name': books_name,
            'books_phone': books_phone,
            'books_address_line1': books_addr_line1,
            'books_city': books_city,
            'books_state': books_state,
            'books_zip': books_zip,
        })
        
        # Preparer info
        if prep_firm:
            firm_ein = safe_text(prep_firm, '{http://www.irs.gov/efile}PreparerFirmEIN')
            firm_name = safe_text(prep_firm, '{http://www.irs.gov/efile}PreparerFirmName/{http://www.irs.gov/efile}BusinessNameLine1Txt')
            prep_addr = prep_firm.find('{http://www.irs.gov/efile}PreparerUSAddress')
            prep_addr_line1 = safe_text(prep_addr, '{http://www.irs.gov/efile}AddressLine1Txt') if prep_addr else ""
            prep_city = safe_text(prep_addr, '{http://www.irs.gov/efile}CityNm') if prep_addr else ""
            prep_state = safe_text(prep_addr, '{http://www.irs.gov/efile}StateAbbreviationCd') if prep_addr else ""
            prep_zip = safe_text(prep_addr, '{http://www.irs.gov/efile}ZIPCd') if prep_addr else ""
            
            prep_person_name = safe_text(prep_person, '{http://www.irs.gov/efile}PreparerPersonNm') if prep_person else ""
            ptin = safe_text(prep_person, '{http://www.irs.gov/efile}PTIN') if prep_person else ""
            prep_phone = safe_text(prep_person, '{http://www.irs.gov/efile}PhoneNum') if prep_person else ""
            
            preparers.append({
                'preparer_id': foundation_id,
                'foundation_id': foundation_id,
                'source_xml_file': xml_filename,
                'firm_ein': firm_ein,
                'firm_name': firm_name,
                'person_name': prep_person_name,
                'ptin': ptin,
                'phone': prep_phone,
                'address_line1': prep_addr_line1,
                'city': prep_city,
                'state': prep_state,
                'zip': prep_zip,
            })
        
        # Officers/Directors
        officer_list = root.findall('.//{http://www.irs.gov/efile}OfficerDirTrstKeyEmplInfoGrp')
        for idx, off in enumerate(officer_list):
            off_name = safe_text(off, '{http://www.irs.gov/efile}PersonNm')
            off_title = safe_text(off, '{http://www.irs.gov/efile}TitleTxt')
            off_hours = safe_text(off, '{http://www.irs.gov/efile}AverageHrsPerWkDevotedToPosRt')
            off_comp = safe_text(off, '{http://www.irs.gov/efile}CompensationAmt')
            off_benefits = safe_text(off, '{http://www.irs.gov/efile}EmployeeBenefitProgramAmt')
            off_expense = safe_text(off, '{http://www.irs.gov/efile}ExpenseAccountOtherAllwncAmt')
            
            off_addr = off.find('{http://www.irs.gov/efile}USAddress')
            off_addr_line1 = safe_text(off_addr, '{http://www.irs.gov/efile}AddressLine1Txt') if off_addr else ""
            off_city = safe_text(off_addr, '{http://www.irs.gov/efile}CityNm') if off_addr else ""
            off_state = safe_text(off_addr, '{http://www.irs.gov/efile}StateAbbreviationCd') if off_addr else ""
            off_zip = safe_text(off_addr, '{http://www.irs.gov/efile}ZIPCd') if off_addr else ""
            
            officers.append({
                'officer_id': f"{foundation_id}_{idx}",
                'foundation_id': foundation_id,
                'source_xml_file': xml_filename,
                'person_name': off_name,
                'title': off_title,
                'address_line1': off_addr_line1,
                'city': off_city,
                'state': off_state,
                'zip': off_zip,
                'hours_per_week': off_hours,
                'compensation': off_comp,
                'employee_benefits': off_benefits,
                'expense_account': off_expense,
            })
        
        # Financial Summary
        form990pf = root.find('.//{http://www.irs.gov/efile}IRS990PF')
        if form990pf:
            balance_sheet = form990pf.find('{http://www.irs.gov/efile}Form990PFBalanceSheetsGrp')
            revenue = form990pf.find('{http://www.irs.gov/efile}AnalysisOfRevenueAndExpenses')
            
            total_revenue = safe_text(revenue, '{http://www.irs.gov/efile}TotalRevAndExpnssAmt') if revenue else "0"
            total_expenses = safe_text(revenue, '{http://www.irs.gov/efile}TotalExpensesRevAndExpnssAmt') if revenue else "0"
            net_income = safe_text(revenue, '{http://www.irs.gov/efile}ExcessRevenueOverExpensesAmt') if revenue else "0"
            
            total_assets_boy = safe_text(balance_sheet, '{http://www.irs.gov/efile}TotalAssetsBOYAmt') if balance_sheet else "0"
            total_assets_eoy = safe_text(balance_sheet, '{http://www.irs.gov/efile}TotalAssetsEOYAmt') if balance_sheet else "0"
            total_liabilities_eoy = safe_text(balance_sheet, '{http://www.irs.gov/efile}TotalLiabilitiesEOYAmt') if balance_sheet else "0"
            cash_boy = safe_text(balance_sheet, '{http://www.irs.gov/efile}CashBOYAmt') if balance_sheet else "0"
            cash_eoy = safe_text(balance_sheet, '{http://www.irs.gov/efile}CashEOYAmt') if balance_sheet else "0"
            
            financials.append({
                'financial_id': foundation_id,
                'foundation_id': foundation_id,
                'source_xml_file': xml_filename,
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'net_income': net_income,
                'total_assets_boy': total_assets_boy,
                'total_assets_eoy': total_assets_eoy,
                'total_liabilities_eoy': total_liabilities_eoy,
                'cash_boy': cash_boy,
                'cash_eoy': cash_eoy,
            })
        
        # Contributors (Schedule B)
        contrib_list = root.findall('.//{http://www.irs.gov/efile}ContributorInfo')
        for idx, contrib in enumerate(contrib_list):
            contrib_name = safe_text(contrib, '{http://www.irs.gov/efile}ContributorBusinessName') or safe_text(contrib, '{http://www.irs.gov/efile}ContributorPersonNm')
            contrib_amount = safe_text(contrib, '{http://www.irs.gov/efile}TotalContributionsAmt')
            
            contrib_addr = contrib.find('{http://www.irs.gov/efile}ContributorUSAddress')
            contrib_addr_line1 = safe_text(contrib_addr, '{http://www.irs.gov/efile}AddressLine1Txt') if contrib_addr else ""
            contrib_city = safe_text(contrib_addr, '{http://www.irs.gov/efile}CityNm') if contrib_addr else ""
            contrib_state = safe_text(contrib_addr, '{http://www.irs.gov/efile}StateAbbreviationCd') if contrib_addr else ""
            contrib_zip = safe_text(contrib_addr, '{http://www.irs.gov/efile}ZIPCd') if contrib_addr else ""
            
            contributors.append({
                'contributor_id': f"{foundation_id}_{idx}",
                'foundation_id': foundation_id,
                'source_xml_file': xml_filename,
                'contributor_name': contrib_name,
                'address_line1': contrib_addr_line1,
                'city': contrib_city,
                'state': contrib_state,
                'zip': contrib_zip,
                'total_contributions': contrib_amount,
            })
        
        # Program Activities
        activity_list = root.findall('.//{http://www.irs.gov/efile}SummaryOfDirectChrtblActyGrp')
        for idx, activity in enumerate(activity_list):
            activity_desc = safe_text(activity, '{http://www.irs.gov/efile}Description1Txt')
            activity_exp = safe_text(activity, '{http://www.irs.gov/efile}Expenses1Amt')
            
            activities.append({
                'activity_id': f"{foundation_id}_{idx}",
                'foundation_id': foundation_id,
                'source_xml_file': xml_filename,
                'description': activity_desc,
                'expenses': activity_exp,
            })
        
        # Other Expenses
        other_exp_list = root.findall('.//{http://www.irs.gov/efile}OtherExpensesSchedule')
        for idx, exp in enumerate(other_exp_list):
            exp_desc = safe_text(exp, '{http://www.irs.gov/efile}Desc')
            exp_amt = safe_text(exp, '{http://www.irs.gov/efile}RevenueAndExpensesPerBooksAmt')
            
            other_expenses.append({
                'expense_id': f"{foundation_id}_{idx}",
                'foundation_id': foundation_id,
                'source_xml_file': xml_filename,
                'description': exp_desc,
                'amount': exp_amt,
            })
        
        # Professional Fees
        prof_fee_list = root.findall('.//{http://www.irs.gov/efile}OtherProfessionalFeesSchedule')
        for idx, fee in enumerate(prof_fee_list):
            fee_category = safe_text(fee, '{http://www.irs.gov/efile}CategoryTxt')
            fee_amt = safe_text(fee, '{http://www.irs.gov/efile}Amt')
            
            professional_fees.append({
                'fee_id': f"{foundation_id}_{idx}",
                'foundation_id': foundation_id,
                'source_xml_file': xml_filename,
                'category': fee_category,
                'amount': fee_amt,
            })
        
        return True
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        traceback.print_exc()
        return False

# Process files
print(f"Processing up to {max_files} XML files...")
xml_files = sorted(Path(xml_folder).glob("*_public.xml"))[:max_files]

for idx, xml_file in enumerate(xml_files, 1):
    success = parse_xml(xml_file, idx)
    if success:
        print(f"✓ {idx}. {xml_file.name}")
    else:
        print(f"✗ {idx}. {xml_file.name} (failed)")

print(f"\nCreating Excel file...")

# Create Excel workbook
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    pd.DataFrame(foundations).to_excel(writer, sheet_name='Foundations', index=False)
    pd.DataFrame(preparers).to_excel(writer, sheet_name='Preparers', index=False)
    pd.DataFrame(officers).to_excel(writer, sheet_name='Officers', index=False)
    pd.DataFrame(financials).to_excel(writer, sheet_name='Financials', index=False)
    pd.DataFrame(contributors).to_excel(writer, sheet_name='Contributors', index=False)
    pd.DataFrame(activities).to_excel(writer, sheet_name='Activities', index=False)
    pd.DataFrame(other_expenses).to_excel(writer, sheet_name='Other_Expenses', index=False)
    pd.DataFrame(professional_fees).to_excel(writer, sheet_name='Professional_Fees', index=False)

print(f"✓ Excel file created: {output_excel}")
print(f"\nData Summary:")
print(f"  Foundations: {len(foundations)}")
print(f"  Preparers: {len(preparers)}")
print(f"  Officers: {len(officers)}")
print(f"  Financials: {len(financials)}")
print(f"  Contributors: {len(contributors)}")
print(f"  Activities: {len(activities)}")
print(f"  Other Expenses: {len(other_expenses)}")
print(f"  Professional Fees: {len(professional_fees)}")
