*** Settings ***
Resource    ../keywords/common.resource
Test Setup    Start Site
Test Teardown    Close Browser

*** Test Cases ***
Site Aberto Com Navbar
    [Tags]    smoke
    Wait For Elements State    header.navbar    visible    ${GLOBAL_TIMEOUT}
    Get Text    header.navbar    contains    ScanDoc

Não Logado É Redirecionado Para Login
    [Tags]    smoke
    Go To    ${BASE_URL}/
    Wait For Elements State    h2:has-text("Entrar")    visible    ${GLOBAL_TIMEOUT}

Página De Login Renderiza
    [Tags]    smoke
    Go To    ${BASE_URL}/login
    Wait For Elements State    input[type=email]    visible
    Wait For Elements State    input[type=password]    visible
    Wait For Elements State    button:has-text("Entrar")    visible
    Wait For Elements State    button:has-text("Continuar com Google")    visible

Página De Cadastro Renderiza
    [Tags]    smoke
    Go To    ${BASE_URL}/register
    Wait For Elements State    h2:has-text("Criar conta")    visible
    Wait For Elements State    input[type=email]    visible
    Wait For Elements State    input[type=password]    visible
    Get Text    body    contains    1 análise por dia

Página De Planos Renderiza
    [Tags]    smoke
    Go To    ${BASE_URL}/planos
    Wait For Elements State    h2:has-text("Planos")    visible    ${GLOBAL_TIMEOUT}
    Wait For Elements State    .plan-card >> nth=0    visible    ${GLOBAL_TIMEOUT}
    ${count}    Get Element Count    .plan-card
    Should Be True    ${count} >= 3    Poucos planos renderizados (${count})
