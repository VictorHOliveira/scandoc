*** Settings ***
Resource    ../keywords/common.resource
Test Setup    Start Site
Test Teardown    Close Browser

*** Test Cases ***
Scan Completo Com PDF
    [Tags]    scan
    ${email}    Generate Test Email
    Register New User    ${email}
    Upload File By Selector    input[type=file]    ${DATA_DIR}/scanme.pdf
    Wait For Elements State    .scan-progress    visible    ${GLOBAL_TIMEOUT}
    Wait For Elements State    .result-head    visible    ${SCAN_TIMEOUT}
    Get Text    .result-head    contains    scanme.pdf
    Wait For Elements State    button:has-text("Achados")    visible
    Wait For Elements State    button:has-text("Texto oculto")    visible
