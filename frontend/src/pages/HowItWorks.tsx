import { Link } from "react-router-dom";
import StaticPage from "./StaticPage";

export default function HowItWorks() {
  return (
    <StaticPage title="Como funciona">
      <h3>O que é o ScanDoc?</h3>
      <p>
        O ScanDoc analisa documentos digitais em busca de técnicas usadas para esconder conteúdo ou
        manipular quem processa aquele arquivo — especialmente sistemas de IA. É útil para conferir
        PDFs, contratos, currículos e outros documentos recebidos por e-mail ou download.
      </p>

      <h3>O que o ScanDoc detecta</h3>
      <ul>
        <li>
          <strong>Texto oculto</strong> — trechos invisíveis (mesma cor do fundo, transparentes, fora
          da área de visualização) presentes em PDFs, DOCX, HTML e imagens.
        </li>
        <li>
          <strong>Microtexto</strong> — texto em fonte muito pequena, difícil de ler a olho nu.
        </li>
        <li>
          <strong>Prompt injection</strong> — instruções escondidas ou visíveis que tentam redirecionar
          um sistema de IA que vá processar o documento.
        </li>
        <li>
          <strong>Unicode suspeito</strong> — caracteres invisíveis ou letras similares (homóglifos)
          usados para mascarar conteúdo.
        </li>
      </ul>

      <h3>Como usar</h3>
      <ol>
        <li>
          <Link to="/register">Crie sua conta</Link> (gratuita).
        </li>
        <li>
          Envie um documento — aceitamos <strong>PDF, DOCX, HTML, imagens (PNG/JPG) e texto</strong>.
        </li>
        <li>
          Em alguns segundos, o ScanDoc gera um relatório com a <strong>pontuação de risco</strong>,
          os achados localizados e o texto oculto extraído.
        </li>
      </ol>

      <h3>Limites e planos</h3>
      <p>
        O plano gratuito permite 1 análise a cada 24 horas. Os planos pagos aumentam esse limite até
        análises ilimitadas. Veja os detalhes na página de{" "}
        <Link to="/planos">Planos</Link>.
      </p>

      <h3>Privacidade</h3>
      <p>
        O documento enviado é processado em memória e <strong>descartado</strong> logo após a
        análise — o ScanDoc não guarda o conteúdo dos arquivos. Saiba mais na{" "}
        <Link to="/privacidade">Política de Privacidade</Link>.
      </p>

      <p className="hint">
        Quer testar agora? <Link to="/register">Crie sua conta</Link> ou{" "}
        <Link to="/login">entre</Link> e envie um documento.
      </p>
    </StaticPage>
  );
}
