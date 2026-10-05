# Monitor de ingressos — Flamengo x Estudiantes (22/10/2026)

Robô que vigia o site do Flamengo a cada 10 minutos e dispara no seu Telegram
assim que a página de venda de ingressos da semifinal for publicada.

Roda no GitHub Actions. **Custo zero, sem servidor, sem cartão de crédito.**

---

## Instalação — 12 minutos

### 1. Criar o bot do Telegram (3 min)

1. No Telegram, abra conversa com **@BotFather**
2. Mande `/newbot`
3. Escolha um nome (ex.: `Monitor Fla`) e um usuário terminado em `bot`
   (ex.: `monitor_fla_wk_bot`)
4. O BotFather devolve um **token** no formato `8123456789:AAF...`. Guarde.

### 2. Descobrir seu chat ID (2 min)

1. Procure o bot que você acabou de criar e mande qualquer mensagem (`oi`)
2. Abra no navegador, trocando `SEU_TOKEN`:

   ```
   https://api.telegram.org/botSEU_TOKEN/getUpdates
   ```

3. Procure `"chat":{"id":123456789` — esse número é o seu **chat ID**

> Se vier `{"ok":true,"result":[]}`, você não mandou a mensagem para o bot ainda.

### 3. Criar o repositório (4 min)

1. No GitHub: **New repository** → nome `monitor-ingressos` → **Public**
   (público dá minutos ilimitados de Actions; privado tem cota mensal)
2. Suba os quatro arquivos desta pasta, mantendo a estrutura:

   ```
   monitor.py
   requirements.txt
   README.md
   .github/workflows/monitor.yml
   ```

> Pelo navegador: **Add file → Upload files**. Para criar a pasta do workflow,
> use **Add file → Create new file** e digite o caminho completo
> `.github/workflows/monitor.yml` no campo do nome.

### 4. Cadastrar os segredos (2 min)

No repositório: **Settings → Secrets and variables → Actions → New repository secret**

| Nome | Valor |
|---|---|
| `TELEGRAM_TOKEN` | o token do BotFather |
| `TELEGRAM_CHAT_ID` | o número do passo 2 |

### 5. Ligar (1 min)

1. Aba **Actions** → clique em **I understand my workflows, go ahead and enable them**
2. **Monitor de ingressos** → **Run workflow** → **Run workflow**
3. Em ~40 segundos você recebe **"✅ Monitor ligado"** no Telegram

Se essa mensagem chegou, está funcionando. Não precisa mexer em mais nada.

---

## O que você vai receber

| Situação | Mensagem |
|---|---|
| Saiu a venda do jogo da semifinal | 🚨 alerta em destaque com o link direto |
| Saiu venda de outro jogo | 🔔 aviso simples |
| Nada aconteceu | 🤖 um "estou vivo" por dia, às 9h |
| O site do Flamengo saiu do ar | ⚠️ aviso, no máximo 1x por dia |

O heartbeat diário existe de propósito: robô que falha calado é pior que
robô nenhum. Se você parar de receber o "estou vivo", desconfie.

---

## Ajustes

**Checar com mais frequência na reta final** — em `.github/workflows/monitor.yml`,
troque `*/10` por `*/5` (mínimo permitido pelo GitHub).

**Monitorar outro jogo depois** — em `monitor.py`, edite `TERMOS_URGENTES`.

**Desligar** — aba Actions → Monitor de ingressos → `...` → Disable workflow.

---

## Limitações, sem enrolação

- O cron do GitHub Actions **não é pontual**: em horário de pico pode atrasar
  5–15 minutos. Para avisar da *abertura* da venda (que dura horas), é de sobra.
  Não serve para disputar segundo a segundo.
- O robô lê a **seção de notícias/ingressos** do site, que é onde o clube sempre
  publica o comunicado antes de abrir a venda. Ele não consegue ler o
  `ingressos.flamengo.com.br` em si, que é uma aplicação JavaScript.
- Se o Flamengo reformular o site, o seletor pode quebrar. O aviso de falha
  cobre esse caso.
- **Não testei contra o site real** — o ambiente onde montei isso não tem acesso
  externo. A lógica foi testada com páginas simuladas. O passo 5 é justamente
  a validação: se chegar o "Monitor ligado", está lendo o site de verdade.

---

## E o preço da passagem?

Não construa robô para isso. Já existe coisa melhor e de graça:

1. **Google Flights** → busque AJU → RIO, 22/10 a 23/10 → ligue **"Acompanhar
   preços"** (o botão de alerta). Chega e-mail a cada variação.
2. Repita para **SSA → RIO** e **MCZ → RIO**, só para ter a referência.
3. **Kayak** → mesma busca → **Price Alert**, como segunda fonte.

Scraper de passagem aérea é briga perdida: Gol, Latam e Azul têm proteção
antibot pesada, e Google Flights bloqueia acesso automatizado. Você gastaria
um fim de semana para ter algo pior que o alerta nativo.

Onde o robô ganha é no ingresso — ali **não existe alerta oficial nenhum**.
É exatamente a lacuna que ele cobre.
