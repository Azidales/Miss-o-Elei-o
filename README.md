# Apuração Missão 2026

App de um único arquivo HTML que mostra, em ranking, a apuração do 1º turno das Eleições 2026 (04/10/2026) só para os candidatos do partido nº 14 (Missão), em todos os cargos e nas 27 UFs. Os dados vêm dos arquivos JSON oficiais do TSE.

| Arquivo | O que é |
|---|---|
| `index.html` | O app (HTML + CSS + JavaScript puro, sem dependências). Abra com duplo clique ou pelo GitHub Pages. |
| `proxy_tse.py` | Proxy local opcional (Python 3.8+, só biblioteca padrão), para quando o navegador bloquear o acesso direto ao TSE (CORS). |

## Uso normal

- **Online (GitHub Pages):** https://azidales.github.io/Miss-o-Elei-o/
- **No PC:** dê duplo clique em `index.html`.

O app lê a configuração do TSE, baixa os resultados e se atualiza sozinho (padrão de 60 s, ajustável em **Ajustes**). Cada navegador faz as próprias requisições ao TSE, então os limites de acesso valem por IP de quem está assistindo.

## Publicar no GitHub Pages

1. No repositório, abra **Settings** e, na barra lateral, clique em **Pages**.
2. Em **Build and deployment**, escolha **Deploy from a branch**.
3. Selecione o branch `claude/missao-2026-apuracao-app-u9eg0u` e a pasta `/ (root)`, e clique em **Save**.

O site fica em `https://azidales.github.io/Miss-o-Elei-o/`. O arquivo `.nojekyll` faz o GitHub publicar os arquivos como estão, sem processamento.

## Se aparecer o aviso "Não foi possível ler os arquivos do TSE" (CORS)

1. Coloque `proxy_tse.py` e `index.html` na mesma pasta do seu computador.
2. Abra o terminal nessa pasta e rode `python proxy_tse.py` (macOS/Linux: `python3 proxy_tse.py`).
3. Acesse `http://localhost:8765` (o navegador abre sozinho) e deixe o terminal aberto. Para encerrar, use Ctrl+C.

O proxy só aceita URLs `https` de `resultados.tse.jus.br` e `resultados-sim.tse.jus.br`, escuta apenas em `127.0.0.1` e limita o repasse a 10 requisições/s.

## Como o app consulta o TSE

- Lê `<base>/<ambiente>/comum/config/ele-c.json` (EA11). Ciclo, pleito, códigos de eleição, cargos e diretórios saem desse arquivo. O app escolhe o pleito mais recente que tenha eleição ordinária federal ou estadual de 1º turno.
- A cada ciclo, baixa primeiro os `br-e<eleição>-ab.json` (EA14), que trazem a data e a hora de totalização de cada UF. Depois baixa os `-u.json` (EA20) só das UFs em que esses valores mudaram.
- Arquivos consultados: Presidente (cargo 1) somente em `br`; Governador (3), Senador (5) e Deputado Federal (6) nas 27 UFs; Deputado Estadual (7) nas 26 UFs sem o DF; Deputado Distrital (8) somente no DF.
- As requisições saem uma de cada vez, com pausa mínima de 150 ms entre elas (cerca de 6,6 por segundo; o limite do TSE é 100 por segundo por IP). O navegador revalida os arquivos por ETag, e as respostas 304 também contam no limite.
- Em caso de erro HTTP, o app não repete na hora: espera o próximo ciclo e mostra um aviso na barra de status. Se receber HTTP 429 ou 403, para todas as requisições por 11 minutos. Um arquivo que dá 404 fica de fora por 5 ciclos, e depois de 5 respostas 404 o ciclo é interrompido.
- Fotos: `<base>/<ambiente>/<ciclo>/<eleição>/fotos/<uf>/<sqcand>.jpeg`. Cada foto só é baixada quando o cartão aparece na tela, e passa pela mesma fila das outras requisições. Se a foto falhar, o cartão mostra as iniciais.

## Ranking

- Critérios: % de votos (`pvap`), Situação, Posição na disputa e Votos absolutos (`vap`).
- A posição na disputa é calculada com todos os candidatos do mesmo arquivo (mesmo cargo e UF), em ordem de votos. Os empates são resolvidos pelo `seq` do TSE.
- Nos cargos majoritários, o card mostra a diferença para a última vaga que elege ou que leva ao 2º turno. Em Presidente e Governador, essa vaga é o 2º lugar. Em Senador, é a posição igual ao número de vagas (`nv`), que em 2026 é 2.
- O ambiente Simulado usa `https://resultados-sim.tse.jus.br/simulado` com o ambiente `simulado2026`. Como lá não existe o partido 14, o número padrão é 57, que tem candidatos em 2º turno, eleitos e suplentes. Dá para trocar o número em **Ajustes**.

Dados oficiais do TSE. App independente, sem vínculo com a Justiça Eleitoral.
