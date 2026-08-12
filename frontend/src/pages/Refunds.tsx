import { Link } from "react-router-dom";
import StaticPage from "./StaticPage";

export default function Refunds() {
  return (
    <StaticPage title="Política de Cancelamento e Reembolso" updated="11/08/2026">
      <h3>1. Assinatura mensal</h3>
      <p>
        Os planos pagos do ScanDoc são assinaturas mensais recorrentes, cobradas via Stripe. A cada
        mês, na mesma data da assinatura, o valor do plano é cobrado no cartão cadastrado.
      </p>

      <h3>2. Como cancelar</h3>
      <p>
        Você pode cancelar a assinatura a qualquer momento na página <strong>Conta</strong> do
        serviço ou entrando em contato pelo e-mail indicado abaixo. Após o cancelamento, a cobrança
        recorrente é encerrada e você mantém o acesso ao plano até o fim do período já pago.
      </p>

      <h3>3. Reembolsos</h3>
      <p>
        Não realizamos reembolso proporcional por períodos parciais já cobrados, pois o acesso é
        mantido até o fim do período pago. Exceções são avaliadas caso a caso:
      </p>
      <ul>
        <li>cobrança duplicada ou cobrança indevida;</li>
        <li>falha técnica comprovada que tenha impedido o uso do serviço;</li>
        <li>conforme exigido pela legislação brasileira aplicável.</li>
      </ul>
      <p>
        Para solicitar um reembolso, envie o comprovante da cobrança e a descrição do ocorrido para
        o e-mail de contato. Analisaremos e responderemos em até 7 dias úteis.
      </p>

      <h3>4. Plano gratuito</h3>
      <p>
        O plano gratuito não tem cobrança e pode ser cancelado simplesmente encerrando o uso ou
        excluindo a conta.
      </p>

      <h3>5. Pagamentos</h3>
      <p>
        Todas as transações são processadas pela Stripe. Estornos e contestações ("chargebacks") são
        tratados conforme as regras da Stripe e da operadora do cartão.
      </p>

      <h3>6. Contato</h3>
      <p>
        E-mail para cancelamento, reembolso e dúvidas de cobrança:{" "}
        <strong>contato@letrindomavel.com</strong>.
      </p>

      <p className="hint">
        Leia também os <Link to="/termos">Termos de Uso</Link> e a{" "}
        <Link to="/privacidade">Política de Privacidade</Link>.
      </p>
    </StaticPage>
  );
}
