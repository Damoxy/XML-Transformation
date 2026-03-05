import os
import xml.etree.ElementTree as ET
from pathlib import Path
import pyodbc
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Configuration
xml_folder = r"D:\XMLs\XMLs\2020\extracted" # 2024,2025,2026 done
max_files = None  # None = all files

# Database Configuration
DB_SERVER = os.getenv('DB_SERVER')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DRIVER = os.getenv('DB_DRIVER')
DB_NAME = os.getenv('DB_NAME')

# Namespace
ns = {'': 'http://www.irs.gov/efile'}

# Data storage - one row per XML file
all_data = []

def safe_text(element, xpath):
    """Safely extract text from XML element"""
    try:
        if element is None:
            return None
        found = element.find(xpath, ns)
        return found.text if found is not None else None
    except:
        return None

def parse_xml(xml_path):
    """Parse single XML file and extract all available data"""
    try:
        xml_filename = Path(xml_path).name
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Initialize record with source file
        record = {'source_xml_file': xml_filename}
        
        # ReturnHeader
        header = root.find('{http://www.irs.gov/efile}ReturnHeader')
        if header is None:
            return None
            
        # Basic header fields
        record['ReturnTs'] = safe_text(header, '{http://www.irs.gov/efile}ReturnTs')
        record['TaxPeriodEndDt'] = safe_text(header, '{http://www.irs.gov/efile}TaxPeriodEndDt')
        record['TaxPeriodBeginDt'] = safe_text(header, '{http://www.irs.gov/efile}TaxPeriodBeginDt')
        record['ReturnTypeCd'] = safe_text(header, '{http://www.irs.gov/efile}ReturnTypeCd')
        record['TaxYr'] = safe_text(header, '{http://www.irs.gov/efile}TaxYr')
        
        # Filer information
        filer = header.find('{http://www.irs.gov/efile}Filer')
        if filer is not None:
            record['Filer_EIN'] = safe_text(filer, '{http://www.irs.gov/efile}EIN')
            record['Filer_BusinessNameLine1Txt'] = safe_text(filer, '{http://www.irs.gov/efile}BusinessName/{http://www.irs.gov/efile}BusinessNameLine1Txt')
            record['Filer_BusinessNameLine2Txt'] = safe_text(filer, '{http://www.irs.gov/efile}BusinessName/{http://www.irs.gov/efile}BusinessNameLine2Txt')
            record['Filer_BusinessNameControlTxt'] = safe_text(filer, '{http://www.irs.gov/efile}BusinessNameControlTxt')
            record['Filer_PhoneNum'] = safe_text(filer, '{http://www.irs.gov/efile}PhoneNum')
            
            # Filer Address
            filer_addr = filer.find('{http://www.irs.gov/efile}USAddress')
            if filer_addr is not None:
                record['Filer_AddressLine1Txt'] = safe_text(filer_addr, '{http://www.irs.gov/efile}AddressLine1Txt')
                record['Filer_AddressLine2Txt'] = safe_text(filer_addr, '{http://www.irs.gov/efile}AddressLine2Txt')
                record['Filer_CityNm'] = safe_text(filer_addr, '{http://www.irs.gov/efile}CityNm')
                record['Filer_StateAbbreviationCd'] = safe_text(filer_addr, '{http://www.irs.gov/efile}StateAbbreviationCd')
                record['Filer_ZIPCd'] = safe_text(filer_addr, '{http://www.irs.gov/efile}ZIPCd')
        
        # Preparer Firm
        prep_firm = header.find('{http://www.irs.gov/efile}PreparerFirmGrp')
        if prep_firm is not None:
            record['PreparerFirm_EIN'] = safe_text(prep_firm, '{http://www.irs.gov/efile}PreparerFirmEIN')
            record['PreparerFirm_BusinessNameLine1Txt'] = safe_text(prep_firm, '{http://www.irs.gov/efile}PreparerFirmName/{http://www.irs.gov/efile}BusinessNameLine1Txt')
            record['PreparerFirm_BusinessNameLine2Txt'] = safe_text(prep_firm, '{http://www.irs.gov/efile}PreparerFirmName/{http://www.irs.gov/efile}BusinessNameLine2Txt')
            
            prep_firm_addr = prep_firm.find('{http://www.irs.gov/efile}PreparerUSAddress')
            if prep_firm_addr is not None:
                record['PreparerFirm_AddressLine1Txt'] = safe_text(prep_firm_addr, '{http://www.irs.gov/efile}AddressLine1Txt')
                record['PreparerFirm_AddressLine2Txt'] = safe_text(prep_firm_addr, '{http://www.irs.gov/efile}AddressLine2Txt')
                record['PreparerFirm_CityNm'] = safe_text(prep_firm_addr, '{http://www.irs.gov/efile}CityNm')
                record['PreparerFirm_StateAbbreviationCd'] = safe_text(prep_firm_addr, '{http://www.irs.gov/efile}StateAbbreviationCd')
                record['PreparerFirm_ZIPCd'] = safe_text(prep_firm_addr, '{http://www.irs.gov/efile}ZIPCd')
        
        # Preparer Person
        prep_person = header.find('{http://www.irs.gov/efile}PreparerPersonGrp')
        if prep_person is not None:
            record['PreparerPerson_Nm'] = safe_text(prep_person, '{http://www.irs.gov/efile}PreparerPersonNm')
            record['PreparerPerson_PTIN'] = safe_text(prep_person, '{http://www.irs.gov/efile}PTIN')
            record['PreparerPerson_PhoneNum'] = safe_text(prep_person, '{http://www.irs.gov/efile}PhoneNum')
        
        # Business Officer
        officer = header.find('{http://www.irs.gov/efile}BusinessOfficerGrp')
        if officer is not None:
            record['Officer_PersonNm'] = safe_text(officer, '{http://www.irs.gov/efile}PersonNm')
            record['Officer_PersonTitleTxt'] = safe_text(officer, '{http://www.irs.gov/efile}PersonTitleTxt')
            record['Officer_PhoneNum'] = safe_text(officer, '{http://www.irs.gov/efile}PhoneNum')
            record['Officer_SignatureDt'] = safe_text(officer, '{http://www.irs.gov/efile}SignatureDt')
        
        # Try IRS990PF first (Form 990-PF)
        form990pf = root.find('.//{http://www.irs.gov/efile}IRS990PF')
        if form990pf is not None:
            # Core financial data from 990-PF
            record['FormType'] = '990-PF'
            
            # Revenue and Expenses
            record['TotalRevAndExpnssAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}AnalysisOfRevenueAndExpenses/{http://www.irs.gov/efile}TotalRevAndExpnssAmt')
            record['TotalExpensesRevAndExpnssAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}AnalysisOfRevenueAndExpenses/{http://www.irs.gov/efile}TotalExpensesRevAndExpnssAmt')
            record['ExcessRevenueOverExpensesAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}AnalysisOfRevenueAndExpenses/{http://www.irs.gov/efile}ExcessRevenueOverExpensesAmt')
            
            # Balance Sheet
            record['TotalAssetsBOYAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}Form990PFBalanceSheetsGrp/{http://www.irs.gov/efile}TotalAssetsBOYAmt')
            record['TotalAssetsEOYAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}Form990PFBalanceSheetsGrp/{http://www.irs.gov/efile}TotalAssetsEOYAmt')
            record['TotalLiabilitiesBOYAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}Form990PFBalanceSheetsGrp/{http://www.irs.gov/efile}TotalLiabilitiesBOYAmt')
            record['TotalLiabilitiesEOYAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}Form990PFBalanceSheetsGrp/{http://www.irs.gov/efile}TotalLiabilitiesEOYAmt')
            record['CashBOYAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}Form990PFBalanceSheetsGrp/{http://www.irs.gov/efile}CashBOYAmt')
            record['CashEOYAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}Form990PFBalanceSheetsGrp/{http://www.irs.gov/efile}CashEOYAmt')
            
            # Minimum investment return
            record['AverageMonthlyFMVOfSecAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}MinimumInvestmentReturnGrp/{http://www.irs.gov/efile}AverageMonthlyFMVOfSecAmt')
            record['MinimumInvestmentReturnAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}MinimumInvestmentReturnGrp/{http://www.irs.gov/efile}MinimumInvestmentReturnAmt')
            
            # Excise Tax
            record['TaxBasedOnInvestmentIncomeAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}ExciseTaxBasedOnInvstIncmGrp/{http://www.irs.gov/efile}TaxBasedOnInvestmentIncomeAmt')
            record['InvestmentIncomeExciseTaxAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}ExciseTaxBasedOnInvstIncmGrp/{http://www.irs.gov/efile}InvestmentIncomeExciseTaxAmt')
            record['CapitalGainNetIncomeAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}CapGainsLossTxInvstIncmDetail/{http://www.irs.gov/efile}CapitalGainNetIncomeAmt')
            
            # Distributable amount
            record['DistributableAsAdjustedAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}DistributableAmountGrp/{http://www.irs.gov/efile}DistributableAsAdjustedAmt')
            record['QualifyingDistributionsAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}PFQualifyingDistributionsGrp/{http://www.irs.gov/efile}QualifyingDistributionsAmt')
            
            # Undistributed income
            record['UndistributedIncomeCYAmt'] = safe_text(form990pf, '{http://www.irs.gov/efile}UndistributedIncomeGrp/{http://www.irs.gov/efile}UndistributedIncomeCYAmt')
            
        else:
            # Try IRS990 (Form 990)
            form990 = root.find('.//{http://www.irs.gov/efile}IRS990')
            if form990 is not None:
                record['FormType'] = '990'
                
                # Revenue
                record['CYContributionsGrantsAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYContributionsGrantsAmt')
                record['CYProgramServiceRevenueAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYProgramServiceRevenueAmt')
                record['CYInvestmentIncomeAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYInvestmentIncomeAmt')
                record['CYOtherRevenueAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYOtherRevenueAmt')
                record['CYTotalRevenueAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYTotalRevenueAmt')
                
                # Expenses
                record['CYGrantsAndSimilarPaidAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYGrantsAndSimilarPaidAmt')
                record['CYSalariesCompEmpBnftPaidAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYSalariesCompEmpBnftPaidAmt')
                record['CYOtherExpensesAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYOtherExpensesAmt')
                record['CYTotalExpensesAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYTotalExpensesAmt')
                record['CYRevenuesLessExpensesAmt'] = safe_text(form990, '{http://www.irs.gov/efile}CYRevenuesLessExpensesAmt')
                
                # Assets
                record['TotalAssetsBOYAmt'] = safe_text(form990, '{http://www.irs.gov/efile}TotalAssetsBOYAmt')
                record['TotalAssetsEOYAmt'] = safe_text(form990, '{http://www.irs.gov/efile}TotalAssetsEOYAmt')
                record['TotalLiabilitiesBOYAmt'] = safe_text(form990, '{http://www.irs.gov/efile}TotalLiabilitiesBOYAmt')
                record['TotalLiabilitiesEOYAmt'] = safe_text(form990, '{http://www.irs.gov/efile}TotalLiabilitiesEOYAmt')
                record['NetAssetsOrFundBalancesBOYAmt'] = safe_text(form990, '{http://www.irs.gov/efile}NetAssetsOrFundBalancesBOYAmt')
                record['NetAssetsOrFundBalancesEOYAmt'] = safe_text(form990, '{http://www.irs.gov/efile}NetAssetsOrFundBalancesEOYAmt')
                
                # Organization info
                record['GrossReceiptsAmt'] = safe_text(form990, '{http://www.irs.gov/efile}GrossReceiptsAmt')
                record['PrincipalOfficerNm'] = safe_text(form990, '{http://www.irs.gov/efile}PrincipalOfficerNm')
                record['WebsiteAddressTxt'] = safe_text(form990, '{http://www.irs.gov/efile}WebsiteAddressTxt')
                record['ActivityOrMissionDesc'] = safe_text(form990, '{http://www.irs.gov/efile}ActivityOrMissionDesc')
                record['TypeOfOrganizationCorpInd'] = safe_text(form990, '{http://www.irs.gov/efile}TypeOfOrganizationCorpInd')
                record['FormationYr'] = safe_text(form990, '{http://www.irs.gov/efile}FormationYr')
                record['LegalDomicileStateCd'] = safe_text(form990, '{http://www.irs.gov/efile}LegalDomicileStateCd')
        
        # Books location (common to both)
        books_elem = root.find('.//{http://www.irs.gov/efile}BooksInCareOfDetail')
        if books_elem is not None:
            record['BooksInCareOf_PersonNm'] = safe_text(books_elem, '{http://www.irs.gov/efile}PersonNm')
            record['BooksInCareOf_PhoneNum'] = safe_text(books_elem, '{http://www.irs.gov/efile}PhoneNum')
            
            books_addr = books_elem.find('{http://www.irs.gov/efile}USAddress')
            if books_addr is not None:
                record['BooksInCareOf_AddressLine1Txt'] = safe_text(books_addr, '{http://www.irs.gov/efile}AddressLine1Txt')
                record['BooksInCareOf_AddressLine2Txt'] = safe_text(books_addr, '{http://www.irs.gov/efile}AddressLine2Txt')
                record['BooksInCareOf_CityNm'] = safe_text(books_addr, '{http://www.irs.gov/efile}CityNm')
                record['BooksInCareOf_StateAbbreviationCd'] = safe_text(books_addr, '{http://www.irs.gov/efile}StateAbbreviationCd')
                record['BooksInCareOf_ZIPCd'] = safe_text(books_addr, '{http://www.irs.gov/efile}ZIPCd')
        
        return record
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return None

# Process files
print(f"Processing XML files from all subdirectories...")
xml_files = sorted(Path(xml_folder).glob("**/*_public.xml"))  # Recursively search all subdirectories
if max_files:
    xml_files = xml_files[:max_files]

successful = 0
failed = 0

for idx, xml_file in enumerate(xml_files, 1):
    record = parse_xml(xml_file)
    if record is not None:
        all_data.append(record)
        successful += 1
        if idx % 50 == 0:
            print(f"✓ Processed {idx} files ({successful} successful, {failed} failed)")
    else:
        failed += 1
        print(f"✗ {xml_file.name} (failed)")

print(f"\nConnecting to database...")
print(f"Server: {DB_SERVER}")
print(f"Database: {DB_NAME}\n")

# SQL query to insert data
insert_query = """
INSERT INTO dbo.IRS_Form990_Records (
    source_xml_file, ReturnTs, TaxPeriodEndDt, TaxPeriodBeginDt, ReturnTypeCd, TaxYr, FormType,
    Filer_EIN, Filer_BusinessNameLine1Txt, Filer_BusinessNameLine2Txt, Filer_BusinessNameControlTxt, 
    Filer_PhoneNum, Filer_AddressLine1Txt, Filer_AddressLine2Txt, Filer_CityNm, Filer_StateAbbreviationCd, 
    Filer_ZIPCd, PreparerFirm_EIN, PreparerFirm_BusinessNameLine1Txt, PreparerFirm_BusinessNameLine2Txt, 
    PreparerFirm_AddressLine1Txt, PreparerFirm_AddressLine2Txt, PreparerFirm_CityNm, 
    PreparerFirm_StateAbbreviationCd, PreparerFirm_ZIPCd, PreparerPerson_Nm, PreparerPerson_PTIN, 
    PreparerPerson_PhoneNum, Officer_PersonNm, Officer_PersonTitleTxt, Officer_PhoneNum, 
    Officer_SignatureDt, BooksInCareOf_PersonNm, BooksInCareOf_PhoneNum, BooksInCareOf_AddressLine1Txt, 
    BooksInCareOf_AddressLine2Txt, BooksInCareOf_CityNm, BooksInCareOf_StateAbbreviationCd, BooksInCareOf_ZIPCd,
    TotalRevAndExpnssAmt, TotalExpensesRevAndExpnssAmt, ExcessRevenueOverExpensesAmt, TotalAssetsBOYAmt, 
    TotalAssetsEOYAmt, TotalLiabilitiesBOYAmt, TotalLiabilitiesEOYAmt, CashBOYAmt, CashEOYAmt, 
    AverageMonthlyFMVOfSecAmt, MinimumInvestmentReturnAmt, TaxBasedOnInvestmentIncomeAmt, 
    InvestmentIncomeExciseTaxAmt, CapitalGainNetIncomeAmt, DistributableAsAdjustedAmt, 
    QualifyingDistributionsAmt, UndistributedIncomeCYAmt, CYContributionsGrantsAmt, 
    CYProgramServiceRevenueAmt, CYInvestmentIncomeAmt, CYOtherRevenueAmt, CYTotalRevenueAmt, 
    CYGrantsAndSimilarPaidAmt, CYSalariesCompEmpBnftPaidAmt, CYOtherExpensesAmt, CYTotalExpensesAmt, 
    CYRevenuesLessExpensesAmt, NetAssetsBOYAmt, NetAssetsEOYAmt, NetAssetsOrFundBalancesBOYAmt, 
    NetAssetsOrFundBalancesEOYAmt, GrossReceiptsAmt, PrincipalOfficerNm, WebsiteAddressTxt, 
    ActivityOrMissionDesc, TypeOfOrganizationCorpInd, FormationYr, LegalDomicileStateCd
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

def insert_record_to_db(conn, record):
    """Insert a single record into the database"""
    try:
        cursor = conn.cursor()
        
        # Order must match the INSERT query columns
        values = (
            record.get('source_xml_file'), record.get('ReturnTs'), record.get('TaxPeriodEndDt'),
            record.get('TaxPeriodBeginDt'), record.get('ReturnTypeCd'), record.get('TaxYr'), 
            record.get('FormType'), record.get('Filer_EIN'), record.get('Filer_BusinessNameLine1Txt'),
            record.get('Filer_BusinessNameLine2Txt'), record.get('Filer_BusinessNameControlTxt'),
            record.get('Filer_PhoneNum'), record.get('Filer_AddressLine1Txt'), 
            record.get('Filer_AddressLine2Txt'), record.get('Filer_CityNm'),
            record.get('Filer_StateAbbreviationCd'), record.get('Filer_ZIPCd'),
            record.get('PreparerFirm_EIN'), record.get('PreparerFirm_BusinessNameLine1Txt'),
            record.get('PreparerFirm_BusinessNameLine2Txt'), record.get('PreparerFirm_AddressLine1Txt'),
            record.get('PreparerFirm_AddressLine2Txt'), record.get('PreparerFirm_CityNm'),
            record.get('PreparerFirm_StateAbbreviationCd'), record.get('PreparerFirm_ZIPCd'),
            record.get('PreparerPerson_Nm'), record.get('PreparerPerson_PTIN'),
            record.get('PreparerPerson_PhoneNum'), record.get('Officer_PersonNm'),
            record.get('Officer_PersonTitleTxt'), record.get('Officer_PhoneNum'),
            record.get('Officer_SignatureDt'), record.get('BooksInCareOf_PersonNm'),
            record.get('BooksInCareOf_PhoneNum'), record.get('BooksInCareOf_AddressLine1Txt'),
            record.get('BooksInCareOf_AddressLine2Txt'), record.get('BooksInCareOf_CityNm'),
            record.get('BooksInCareOf_StateAbbreviationCd'), record.get('BooksInCareOf_ZIPCd'),
            record.get('TotalRevAndExpnssAmt'), record.get('TotalExpensesRevAndExpnssAmt'),
            record.get('ExcessRevenueOverExpensesAmt'), record.get('TotalAssetsBOYAmt'),
            record.get('TotalAssetsEOYAmt'), record.get('TotalLiabilitiesBOYAmt'),
            record.get('TotalLiabilitiesEOYAmt'), record.get('CashBOYAmt'), record.get('CashEOYAmt'),
            record.get('AverageMonthlyFMVOfSecAmt'), record.get('MinimumInvestmentReturnAmt'),
            record.get('TaxBasedOnInvestmentIncomeAmt'), record.get('InvestmentIncomeExciseTaxAmt'),
            record.get('CapitalGainNetIncomeAmt'), record.get('DistributableAsAdjustedAmt'),
            record.get('QualifyingDistributionsAmt'), record.get('UndistributedIncomeCYAmt'),
            record.get('CYContributionsGrantsAmt'), record.get('CYProgramServiceRevenueAmt'),
            record.get('CYInvestmentIncomeAmt'), record.get('CYOtherRevenueAmt'),
            record.get('CYTotalRevenueAmt'), record.get('CYGrantsAndSimilarPaidAmt'),
            record.get('CYSalariesCompEmpBnftPaidAmt'), record.get('CYOtherExpensesAmt'),
            record.get('CYTotalExpensesAmt'), record.get('CYRevenuesLessExpensesAmt'),
            record.get('NetAssetsBOYAmt'), record.get('NetAssetsEOYAmt'),
            record.get('NetAssetsOrFundBalancesBOYAmt'), record.get('NetAssetsOrFundBalancesEOYAmt'),
            record.get('GrossReceiptsAmt'), record.get('PrincipalOfficerNm'),
            record.get('WebsiteAddressTxt'), record.get('ActivityOrMissionDesc'),
            record.get('TypeOfOrganizationCorpInd'), record.get('FormationYr'),
            record.get('LegalDomicileStateCd')
        )
        
        cursor.execute(insert_query, values)
        cursor.close()
        return True
    except Exception as e:
        print(f"  Error inserting record: {e}")
        return False

try:
    # Build connection string
    connection_string = f'Driver={{{DB_DRIVER}}};Server={DB_SERVER};Database={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD};'
    conn = pyodbc.connect(connection_string)
    conn.autocommit = False
    
    # Insert records into database
    db_successful = 0
    db_failed = 0
    
    for idx, record in enumerate(all_data, 1):
        if insert_record_to_db(conn, record):
            db_successful += 1
        else:
            db_failed += 1
        
        if idx % 50 == 0:
            conn.commit()  # Commit every 50 records
            print(f"✓ Inserted {idx} records ({db_successful} successful, {db_failed} failed)")
    
    # Final commit
    conn.commit()
    conn.close()
    
    print(f"\n✓ Successfully loaded data to database")
    print(f"\nData Summary:")
    print(f"  Total rows inserted: {db_successful}")
    print(f"  Failed inserts: {db_failed}")
    print(f"  Total XML files processed: {len(all_data)}")
    print(f"  Database: {DB_NAME}")
    print(f"  Table: IRS_Form990_Records")
    
except Exception as e:
    print(f"\n✗ Database connection error: {e}")
    traceback.print_exc()
    exit(1)
