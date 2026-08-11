import { Link } from "react-router-dom";
import StaticPage from "./StaticPage";

export default function Privacy() {
  return (
    <StaticPage title="Política de Privacidade" updated="11/08/2026">
      <p>
        Esta Política descreve como o ScanDoc coleta, usa e protege as informações pessoais dos
        usuários, em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018 – LGPD).
      </p>

      <h3>1. Dados que coletamos</h3>
      <ul>
        <li>
          <strong>Dados da conta:</strong> nome, e-mail e identificador interno criados ao registrar
          na conta, fornecidos pelo Firebase Authentication (e-mail/senha ou Google).
        </li>
        <li>
          <strong>Metadados de análise:</strong> nome do arquivo, formato, pontuação do relatório e
          data da análise, utilizados para controle de cota e estatísticas de uso.
        </li>
      </ul>

      <h3>2. Documentos enviados</h3>
      <p>
        <strong>O ScanDoc não armazena o conteúdo dos documentos.</strong> O arquivo enviado é
        processado em memória para gerar o relatório de análise e é descartado imediatamente após o
        processamento. Não fazemos cópias, não guardamos o texto extraído e não utilizamos o
        conteúdo dos documentos para qualquer outra finalidade.
      </p>

      <h3>3. Pagamentos</h3>
      <p>
        As assinaturas são processadas pela <strong>Stripe</strong>. Os dados de pagamento (número
        do cartão etc.) são tratados diretamente pela Stripe e nunca passam pelos nossos servidores.
        Ao assinar, os termos e a política de privacidade da Stripe passam a se aplicar ao
        processamento dos seus dados de pagamento.
      </p>

      <h3>4. Autenticação</h3>
      <p>
        O login é gerenciado pelo Firebase Authentication do Google. O Google processa as
        credenciais conforme a{" "}
        <a href="https://policies.google.com/privacy" target="_blank" rel="noreferrer">
          política de privacidade do Google
        </a>
        .
      </p>

      <h3>5. Bases legais</h3>
      <p>
        Tratamos seus dados com base na execução do contrato de uso (prestação do serviço e cobrança
        de assinaturas), no cumprimento de obrigações legais e em nosso legítimo interesse na
        segurança e melhoria do serviço.
      </p>

      <h3>6. Compartilhamento</h3>
      <p>
        Não vendemos nem compartilhamos seus dados pessoais com terceiros, exceto quando necessário
        para operar o serviço (processadores de pagamento e autenticação, acima) ou por obrigação
        legal.
      </p>

      <h3>7. Retenção</h3>
      <p>
        Os dados da conta são mantidos enquanto a conta existir. Os metadados de análise são mantidos
        para fins de cota e estatísticas e podem ser removidos mediante solicitação. Você pode
        excluir sua conta a qualquer momento entrando em contato conosco.
      </p>

      <h3>8. Seus direitos (LGPD)</h3>
      <p>
        Você pode solicitar acesso, correção, portabilidade e exclusão dos seus dados pessoais, bem
        como revogar consentimento, quando aplicável. Para exercer seus direitos, envie uma
        solicitação pelo e-mail de contato abaixo. Responderemos no prazo legal.
      </p>

      <h3>9. Segurança</h3>
      <p>
        Utilizamos HTTPS, autenticação de usuários via tokens do Firebase, restrição de acesso ao
        banco de dados e cabeçalhos de segurança. Não é possível garantir segurança absoluta, mas
        adotamos práticas razoáveis de proteção.
      </p>

      <h3>10. Contato</h3>
      <p>
        Controladora dos dados: ScanDoc. Para questões de privacidade, entre em contato pelo e-mail
        <strong> contato@scandoc.qaoverflow.com</strong>.
      </p>

      <p className="hint">
        Consulte também os <Link to="/termos">Termos de Uso</Link> e a{" "}
        <Link to="/reembolsos">Política de Cancelamento e Reembolso</Link>.
      </p>
    </StaticPage>
  );
}
