*** Settings ***
Library           SeleniumLibrary
Library           OperatingSystem
Library           helper.py

Suite Setup       Open Report
Suite Teardown    Close All Browsers


*** Variables ***
${REPORT_FILE}       ${CURDIR}${/}generated_report${/}report.html
${PARQUET_FOLDER}    ${CURDIR}${/}parquet_data
${FILTER_DATE}       ${EMPTY}


*** Test Cases ***
Compare HTML Report With Parquet Dataset
    ${html_df}=    Wait Until Keyword Succeeds
    ...    5x
    ...    1s
    ...    Read Report Table

    ${parquet_df}=    Read Parquet Data
    ...    ${PARQUET_FOLDER}
    ...    ${FILTER_DATE}

    ${differences}=    Compare Dataframes
    ...    ${html_df}
    ...    ${parquet_df}

    Should Be Empty    ${differences}
    ...    msg=HTML and Parquet data do not match: ${differences}


*** Keywords ***
Open Report
    Open Browser    file://${REPORT_FILE}    Chrome
    Maximize Browser Window


Read Report Table
    Wait Until Element Is Visible    css:.table    timeout=15s
    ${table}=    Get WebElement    css:.table
    ${html_df}=    Read Html Table    ${table}
    RETURN    ${html_df}