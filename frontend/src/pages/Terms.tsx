import { Link } from "react-router-dom";
import StaticPage from "./StaticPage";

export default function Terms() {
  return (
    <StaticPage title="Termos de Uso" updated="11/08/2026">
      <h3>1. Aceitação</h3>
      <p>
        Ao criar uma conta e utilizar o ScanDoc, você concorda com estes Termos de Uso. Se você
        não concordar com qualquer parte deles, não utilize o serviço.
      </p>

      <h3>2. O serviço</h3>
      <p>
        O ScanDoc é uma ferramenta de análise de documentos que detecta texto oculto, microtexto,
        caracteres Unicode suspeitos e possíveis instruções de prompt injection em arquivos PDF,
        DOCX, HTML, imagens e texto. O resultado é apresentado como um relatório de análise.
      </p>

      <h3>3. Conta</h3>
      <p>
        Para usar o serviço é necessário criar uma conta com e-mail e senha ou com sua conta
        Google. Você é responsável por manter a confidencialidade de suas credenciais e por toda
        atividade realizada em sua conta.
      </p>

      <h3>4. Planos e pagamento</h3>
      <p>
        O ScanDoc oferece um plano gratuito com limite de análises e planos pagos com limites
        maiores, cobrados mensalmente via Stripe. Ao assinar um plano pago você autoriza a cobrança
        recorrente mensal. O pagamento é processado pela Stripe; o ScanDoc não armazena dados de
        cartão. Você pode cancelar a assinatura a qualquer momento na página da conta e mantém o
        acesso até o fim do período já pago.
      </p>

      <h3>5. Uso aceitável</h3>
      <p>
        Você concorda em não utilizar o serviço para violar leis, para analisar documentos que não
        tenha direito de processar ou para tentar comprometer a segurança do serviço, de terceiros
        ou da infraestrutura que o suporta.
      </p>

      <h3>6. Documentos enviados</h3>
      <p>
        Os arquivos enviados são processados em memória para gerar o relatório e são descartados em
        seguida. O ScanDoc não armazena o conteúdo dos documentos. Apenas metadados da análise
        (nome do arquivo, formato, pontuação e data) são registrados para controle de cota e
        melhorias do serviço.
      </p>

      <h3>7. Propriedade intelectual</h3>
      <p>
        O software, o design e a marca do ScanDoc pertencem aos seus operadores. O relatório gerado
        é fornecido a você para uso em seus processos; ele não constitui garantia de que um
        documento esteja livre de qualquer técnica de manipulação.
      </p>

      <h3>8. Limitação de responsabilidade</h3>
      <p>
        O serviço é fornecido "no estado em que se encontra". O ScanDoc não garante que a análise
        seja completa ou infalível e não se responsabiliza por decisões tomadas com base nos
        relatórios. Na máxima extensão permitida pela lei, o ScanDoc não será responsável por danos
        indiretos, incidentais ou consequenciais.
      </p>

      <h3>9. Alterações</h3>
      <p>
        Estes Termos podem ser atualizados periodicamente. O uso continuado do serviço após
        alterações significa aceitação dos novos termos.
      </p>

      <h3>10. Contato</h3>
      <p>
        Dúvidas sobre estes Termos podem ser enviadas pelo formulário de contato disponível no
        serviço ou pelo e-mail informado na página de privacidade.
      </p>

      <p className="hint">
        Leia também a nossa{" "}
        <Link to="/privacidade">Política de Privacidade</Link> e a{" "}
        <Link to="/reembolsos">Política de Cancelamento e Reembolso</Link>.
      </p>
    </StaticPage>
  );
}
