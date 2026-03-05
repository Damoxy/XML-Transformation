-- Drop existing table if it exists
IF OBJECT_ID('dbo.IRS_Form990_Records', 'U') IS NOT NULL 
    DROP TABLE dbo.IRS_Form990_Records;
GO

-- Create IRS_Form990_Records table - main table for all return data
CREATE TABLE dbo.IRS_Form990_Records (
    -- Primary Key and metadata
    ReturnID INT PRIMARY KEY IDENTITY(1,1),
    source_xml_file NVARCHAR(255),
    LoadedDateTime DATETIME DEFAULT GETDATE(),
    
    -- Return Header
    ReturnTs NVARCHAR(50),
    TaxPeriodEndDt NVARCHAR(50),
    TaxPeriodBeginDt NVARCHAR(50),
    ReturnTypeCd NVARCHAR(50),
    TaxYr NVARCHAR(50),
    FormType NVARCHAR(50),
    
    -- Filer Information
    Filer_EIN NVARCHAR(50),
    Filer_BusinessNameLine1Txt NVARCHAR(255),
    Filer_BusinessNameLine2Txt NVARCHAR(255),
    Filer_BusinessNameControlTxt NVARCHAR(255),
    Filer_PhoneNum NVARCHAR(50),
    Filer_AddressLine1Txt NVARCHAR(255),
    Filer_AddressLine2Txt NVARCHAR(255),
    Filer_CityNm NVARCHAR(100),
    Filer_StateAbbreviationCd NVARCHAR(10),
    Filer_ZIPCd NVARCHAR(20),
    
    -- Preparer Firm Information
    PreparerFirm_EIN NVARCHAR(50),
    PreparerFirm_BusinessNameLine1Txt NVARCHAR(255),
    PreparerFirm_BusinessNameLine2Txt NVARCHAR(255),
    PreparerFirm_AddressLine1Txt NVARCHAR(255),
    PreparerFirm_AddressLine2Txt NVARCHAR(255),
    PreparerFirm_CityNm NVARCHAR(100),
    PreparerFirm_StateAbbreviationCd NVARCHAR(10),
    PreparerFirm_ZIPCd NVARCHAR(20),
    
    -- Preparer Person Information
    PreparerPerson_Nm NVARCHAR(255),
    PreparerPerson_PTIN NVARCHAR(50),
    PreparerPerson_PhoneNum NVARCHAR(50),
    
    -- Business Officer Information
    Officer_PersonNm NVARCHAR(255),
    Officer_PersonTitleTxt NVARCHAR(255),
    Officer_PhoneNum NVARCHAR(50),
    Officer_SignatureDt NVARCHAR(50),
    
    -- Books In Care Of
    BooksInCareOf_PersonNm NVARCHAR(255),
    BooksInCareOf_PhoneNum NVARCHAR(50),
    BooksInCareOf_AddressLine1Txt NVARCHAR(255),
    BooksInCareOf_AddressLine2Txt NVARCHAR(255),
    BooksInCareOf_CityNm NVARCHAR(100),
    BooksInCareOf_StateAbbreviationCd NVARCHAR(10),
    BooksInCareOf_ZIPCd NVARCHAR(20),
    
    -- Form 990-PF Financial Data
    TotalRevAndExpnssAmt NVARCHAR(50),
    TotalExpensesRevAndExpnssAmt NVARCHAR(50),
    ExcessRevenueOverExpensesAmt NVARCHAR(50),
    TotalAssetsBOYAmt NVARCHAR(50),
    TotalAssetsEOYAmt NVARCHAR(50),
    TotalLiabilitiesBOYAmt NVARCHAR(50),
    TotalLiabilitiesEOYAmt NVARCHAR(50),
    CashBOYAmt NVARCHAR(50),
    CashEOYAmt NVARCHAR(50),
    AverageMonthlyFMVOfSecAmt NVARCHAR(50),
    MinimumInvestmentReturnAmt NVARCHAR(50),
    TaxBasedOnInvestmentIncomeAmt NVARCHAR(50),
    InvestmentIncomeExciseTaxAmt NVARCHAR(50),
    CapitalGainNetIncomeAmt NVARCHAR(50),
    DistributableAsAdjustedAmt NVARCHAR(50),
    QualifyingDistributionsAmt NVARCHAR(50),
    UndistributedIncomeCYAmt NVARCHAR(50),
    
    -- Form 990 Financial Data
    CYContributionsGrantsAmt NVARCHAR(50),
    CYProgramServiceRevenueAmt NVARCHAR(50),
    CYInvestmentIncomeAmt NVARCHAR(50),
    CYOtherRevenueAmt NVARCHAR(50),
    CYTotalRevenueAmt NVARCHAR(50),
    CYGrantsAndSimilarPaidAmt NVARCHAR(50),
    CYSalariesCompEmpBnftPaidAmt NVARCHAR(50),
    CYOtherExpensesAmt NVARCHAR(50),
    CYTotalExpensesAmt NVARCHAR(50),
    CYRevenuesLessExpensesAmt NVARCHAR(50),
    NetAssetsBOYAmt NVARCHAR(50),
    NetAssetsEOYAmt NVARCHAR(50),
    NetAssetsOrFundBalancesBOYAmt NVARCHAR(50),
    NetAssetsOrFundBalancesEOYAmt NVARCHAR(50),
    GrossReceiptsAmt NVARCHAR(50),
    PrincipalOfficerNm NVARCHAR(255),
    WebsiteAddressTxt NVARCHAR(255),
    ActivityOrMissionDesc NVARCHAR(MAX),
    TypeOfOrganizationCorpInd NVARCHAR(50),
    FormationYr NVARCHAR(50),
    LegalDomicileStateCd NVARCHAR(10)
);

PRINT 'Table IRS_Form990_Records created successfully';
GO

-- Create indexes for better query performance
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_EIN')
    CREATE INDEX idx_EIN ON dbo.IRS_Form990_Records(Filer_EIN);

IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_TaxYr')
    CREATE INDEX idx_TaxYr ON dbo.IRS_Form990_Records(TaxYr);

PRINT 'Indexes created successfully';
GO

-- Verify table creation
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'IRS_Form990_Records';
GO
