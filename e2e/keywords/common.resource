*** Settings ***
Library    Browser
Variables    ${CURDIR}/../variables.py

*** Variables ***
${PASSWORD}    e2e-senha-123

*** Keywords ***
Start Site
    New Browser    ${BROWSER}    headless=${HEADLESS}
    New Context
    New Page    ${BASE_URL}
    Wait For Load State    networkidle

Generate Test Email
    ${email}    Evaluate    f"e2e+{int(__import__('time').time()*1000)}+{__import__('uuid').uuid4().hex[:6]}@test.com"
    RETURN    ${email}

Register New User
    [Arguments]    ${email}    ${name}=Usuário Teste
    Go To    ${BASE_URL}/register
    Fill Text    input:not([type])    ${name}
    Fill Text    input[type=email]    ${email}
    Fill Text    input[type=password]    ${PASSWORD}
    Click    button:has-text("Criar conta")
    Wait For Elements State    h2:has-text("Analisar documento")    visible    ${GLOBAL_TIMEOUT}

Login With
    [Arguments]    ${email}    ${password}
    Go To    ${BASE_URL}/login
    Fill Text    input[type=email]    ${email}
    Fill Text    input[type=password]    ${password}
    Click    button:has-text("Entrar")

Logout
    Click    button:has-text("Sair")
    Wait For Elements State    h2:has-text("Entrar")    visible    ${GLOBAL_TIMEOUT}
