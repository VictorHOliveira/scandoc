*** Settings ***
Resource    ../keywords/common.resource
Test Setup    Start Site
Test Teardown    Close Browser

*** Test Cases ***
Registrar Nova Conta
    [Tags]    auth
    ${email}    Generate Test Email
    Register New User    ${email}
    Wait For Elements State    button:has-text("Sair")    visible
    Get Text    body    contains    Cota:

Senha Incorreta Mostra Erro
    [Tags]    auth
    ${email}    Generate Test Email
    Register New User    ${email}
    Logout
    Login With    ${email}    senha-errada-999
    Wait For Elements State    .error-box    visible    ${GLOBAL_TIMEOUT}
    Get Text    .error-box    contains    E-mail ou senha incorretos

Credenciais Inválidas Mostram Erro
    [Tags]    auth
    ${email}    Generate Test Email
    Login With    ${email}    senha-errada-999
    Wait For Elements State    .error-box    visible    ${GLOBAL_TIMEOUT}
    Get Text    .error-box    contains    E-mail ou senha incorretos

Login E Logout
    [Tags]    auth
    ${email}    Generate Test Email
    Register New User    ${email}
    Logout
    Login With    ${email}    ${PASSWORD}
    Wait For Elements State    h2:has-text("Analisar documento")    visible    ${GLOBAL_TIMEOUT}
    Logout
    Wait For Elements State    input[type=email]    visible
