# BlackJack

A small multiplayer Blackjack web app built with Flask, SQLite, HTML, CSS, and JavaScript. It runs in Docker and can be installed as a CasaOS app.

This is a casual play-money game for friends, not a real-money gambling service.

## What persists

The Compose setup stores accounts and admin settings in the named Docker volume `blackjack-data`, mounted at `/data`. Rebuilding or replacing the container keeps that volume. Removing the volume deletes all accounts, balances, and settings, including account-approval and signup preferences.

The admin console is the same web app on the same port:

- App: `http://<server-ip>:3000/`
- Admin console: opens automatically on the home page after an admin signs in

Public signups are disabled by default on a fresh install. The admin can enable or disable them in the Admin Console and can separately require approval for new accounts. When approval is required, new accounts remain pending and cannot sign in until the admin approves them. Existing accounts are not affected.
Admin accounts are omitted from the leaderboard and cannot create or join game rooms.

## Playing with friends

1. Sign in as the admin and enable signups in the Admin Console. Optionally enable **Require Approval** to review each new account before it can sign in.
2. If Cloudflare Access protects the site, allow your friends' identities in its policy so they can reach the game.
3. Share the home-page address. Each friend creates an account with a 3-to-20-character username (letters, numbers, and underscores) and a password of at least 8 characters.
4. If approval is required, open the Admin Console and select **Approve** beside each pending account. Players can then sign in.
5. A player creates a room and shares its room code; the other players sign in and join with that code. Up to five non-admin players can sit at a table.
6. Disable public signups again when everyone has an account.

When a player's balance reaches £0, they can still place a £1 safety bet for a hand. It does not debit the balance; regular win, loss, and push outcomes then apply. While signed in, each player can see their own completed-hand totals and net winnings below the public leaderboard. These stats are private to that player's account.

## Downloadable clients

The [GitHub Releases page](https://github.com/BN208/BlackJack/releases) provides an Android APK, a portable Windows executable, and a Linux Flatpak client. Each client asks for a server address and opens the site inside the app. The address is prefilled with `https://blackjack.bcull.online`; replace it with your own server URL to connect elsewhere.

- **Android:** install the APK from the release. Android may ask you to allow installation from your browser or file manager. The 1.0 APK is signed with the CI debug key for sideload testing.
- **Windows:** run the portable x64 `.exe`.
- **Linux:** install the `.flatpak` bundle with `flatpak install --user BlackJack-1.0.flatpak`. Flatpak may download the Freedesktop runtime the first time.
- **Server hosts:** download `BlackJack-Server-1.0.zip`, extract it on the host, then follow the CasaOS/Docker instructions in its `README.md`. The client packages do not host the game server.

Use an HTTPS address for servers exposed beyond a trusted local network. The clients also accept HTTP addresses for local/LAN testing.

## Requirements

- CasaOS or another Linux host with Docker Engine and the Docker Compose plugin (`docker compose`)
- SSH access to the host, or another way to put the project files on it
- An available host port, 3000 by default

## First installation on CasaOS

### 1. Put the project on the server

You can clone the repository on the server:

```bash
sudo mkdir -p /DATA/AppData/blackjack
sudo chown "$USER":"$(id -gn)" /DATA/AppData/blackjack
git clone https://github.com/BN208/BlackJack.git /DATA/AppData/blackjack
```

Alternatively, copy the project from your computer. Exclude your local `.env` and database so you don't upload laptop credentials or data:

```bash
ssh <user>@<server> 'mkdir -p /DATA/AppData/blackjack'
rsync -av \
  --exclude='.git/' \
  --exclude='.env' \
  --exclude='*.db' \
  --exclude='*.sqlite*' \
  --exclude='account.txt' \
  --exclude='__pycache__/' \
  --exclude='node_modules/' \
  BlackJack/ <user>@<server>:/DATA/AppData/blackjack/
```

Replace `<user>` and `<server>` with your CasaOS SSH username and hostname or IP.

### 2. Configure secrets

On the server:

```bash
cd /DATA/AppData/blackjack
cp .env.example .env
openssl rand -hex 32
nano .env
```

Use the generated random value for `BLACKJACK_SECRET_KEY`. Choose a private `ADMIN_USERNAME` and a strong `ADMIN_PASSWORD`. Set `COOKIE_SECURE=1` when using the app over HTTPS through Cloudflare; use `0` for local HTTP-only testing. Save `.env` and keep it private. It is excluded from Git.

`CLOUDFLARE_TUNNEL_TOKEN` is only needed if you run the optional `cloudflared` Compose service below. A Tunnel ID is not a token. If you already run a connector and will configure the route in the Cloudflare dashboard, you do not need a token for this app.

On the first start, the app creates the configured admin account. If that username already exists in the database, it is granted admin access but keeps its existing password.

### 3. Build and start the app

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 blackjack
```

Open `http://<server-ip>:3000/` and sign in with the admin account. The Admin Console opens automatically without changing the URL. The CasaOS menu opens the app home page; if CasaOS asks for a Web UI URL, use `http://<server-ip>:3000/`.

The service publishes port 3000 on the host. If that port is already in use, change the left side of `"3000:3000"` in `docker-compose.yml` (for example, `"3001:3000"`), then use the new host port in CasaOS and Cloudflare settings.

## Cloudflare Tunnel with an existing connector

1. In the Cloudflare Zero Trust dashboard, open your existing Tunnel and add a Public Hostname for your domain.
2. Set the service to `http://<server-lan-ip>:3000` (or your changed host port). Use the CasaOS server's LAN IP, not `localhost`.
3. Add a Cloudflare Access application and an allow policy restricted to your identity before sharing the hostname.
4. Visit `https://<your-domain>/` and sign in. The Admin Console opens automatically for the admin account.

No router port forwarding is required. The Tunnel connector makes the outbound connection to Cloudflare; the app itself does not need the tunnel token.

### Optional: run a token-based connector in this Compose project

Use this only if you want this project to run its own `cloudflared` connector. Set `CLOUDFLARE_TUNNEL_TOKEN` in `.env`, then run:

```bash
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build
```

In the Cloudflare Tunnel dashboard, route the Public Hostname to `http://blackjack:3000`. Protect the hostname with Cloudflare Access as described above.

## Updating or reinstalling

For code updates or a rebuild, put the new project files in the same directory and run:

```bash
cd /DATA/AppData/blackjack
docker compose up -d --build
```

This rebuilds/replaces the container and preserves the `blackjack-data` volume. You do not need to uninstall or recreate the app. **Do not use `docker compose down -v` for an update**; `-v` deletes the database volume.

To stop and recreate containers without deleting data:

```bash
docker compose down
docker compose up -d --build
```

For a backup, stop the app, copy the database out of the container, then start it again:

```bash
docker compose stop blackjack
docker compose cp blackjack:/data/account.db ./account.db.backup
docker compose start blackjack
```

Keep the backup private; it contains account password hashes and balances. Restore it only with the app stopped:

```bash
docker compose stop blackjack
docker compose cp ./account.db.backup blackjack:/data/account.db
docker compose start blackjack
```

The `*.db` Git ignore rule prevents accidentally committing the backup.

### If you already have an older Git clone

Repository history was cleaned to remove previously committed database and account files. An old clone may not be able to `git pull` the rewritten history. Keep its `.env` safe, get a fresh copy of the project files, and copy the new source over the existing project directory without replacing `.env`. Run `docker compose up -d --build` from that same directory so Compose uses the existing named volume and accounts remain available.

## CasaOS app menu

The Compose file includes CasaOS metadata, including `index: /` and port 3000. Install it through CasaOS's custom-app/Compose install flow if you want CasaOS to register it in the app menu. The Docker build context (`build: .`) must point to the directory containing the project files.

If you start it from an SSH shell and CasaOS does not list it in the menu, use CasaOS's custom-app option and set its Web UI to `http://<server-ip>:3000/`. The web UI and admin console are still served by the same container; signing in as admin opens the console.

## Troubleshooting

- **Compose command not found:** install the Docker Compose plugin for your distribution; `docker-compose` (hyphenated) is an older alternative if already installed.
- **Build takes a long time:** confirm `.dockerignore` is present in the project directory, then retry `docker compose up -d --build`.
- **App does not start:** inspect `docker compose ps` and `docker compose logs --tail=100 blackjack`.
- **Port already allocated:** use another host port in the Compose mapping and update the LAN URL/Cloudflare origin.
- **A new account cannot sign in:** check the account's Approval status in the Admin Console; an admin must approve pending accounts when approval is required.
- **Admin page says signups are disabled:** signups are controlled by the Admin Console toggle, not by reinstalling the container.
- **Admin login fails after changing `.env`:** for an existing database, the configured admin username's old password is retained. Use that password or follow a deliberate password-reset procedure; do not delete the volume to reset it unless you intend to erase all accounts.

## Security notes

- Never commit or share `.env`, database backups, or Cloudflare Tunnel tokens.
- Keep public signup disabled unless you intentionally want new accounts.
- Use Cloudflare Access to restrict the public hostname to your identity; the app's admin APIs independently require an admin account.
- If friends need to play through Cloudflare Access, allow their identities too. A policy allowing only the admin will block them before they reach the app.
- Game rooms are in memory and close when the container restarts. Players in a room can view its state; room membership is required.
- If account files from an earlier repository history were exposed, rotate affected passwords. History rewriting cannot remove copies from forks or existing clones.

## Art credits

Playing-card artwork is by **IvoryRed**, from [Pixel Poker Cards (version 1.3)](https://ivoryred.itch.io/pixel-poker-cards), licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). The [OpenGameArt listing](https://opengameart.org/content/pixel-poker-cards) also identifies IvoryRed as the creator. The card sheet was cropped into individual card images for the game.
