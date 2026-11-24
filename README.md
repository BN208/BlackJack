This is a multiplayer Blackjack app in Python, HTML, CSS, and JavaScript.

## CasaOS / Docker deployment

1. Copy `.env.example` to `.env`.
2. Set a unique `BLACKJACK_SECRET_KEY`, `ADMIN_USERNAME`, and strong `ADMIN_PASSWORD`.
3. Start the service with `docker compose up -d --build`.
4. Open `http://<home-server-ip>:3000`.
5. Sign in with the configured admin credentials. The **Admin** button provides account balance management, account deletion, and a public-signup toggle.

Public signups default to disabled on a fresh install. An admin can enable them from the console; the setting is stored in the `blackjack-data` Docker volume and survives restarts.

## CasaOS app menu

- Copy this repository to the server.
- In CasaOS, use **App Store > Custom Install** (or **My Apps > Install a Custom App**) and upload/import `docker-compose.yml`.
- Keep the persistent volume and set `BLACKJACK_SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` before starting.
- The CasaOS metadata sets the app menu button to open `http://<server-ip>:3000/admin`.
- For a container built on CasaOS, `docker-compose.yml` uses the local build context. Import it from a location visible to the server and run:
  `docker compose up -d --build`

CasaOS App button behavior is metadata-dependent; if the UI ignores `index: /admin`, set the app's Web UI URL to `http://<server-ip>:3000/admin`.

## Cloudflare Tunnel and custom domain

1. Create a Cloudflare Tunnel and copy its token.
2. Set `CLOUDFLARE_TUNNEL_TOKEN` in `.env`.
3. Start both compose files:
   `docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build`
4. In the Cloudflare Zero Trust Tunnel Public Hostname settings, route `https://blackjack.yourdomain.com` to `http://blackjack:3000`.
5. Set `COOKIE_SECURE=1` in the environment and restart the app.

The Cloudflare Tunnel does not publish a public server port. It provides outbound-only access to the Docker service.

To make the service private to you, create a Cloudflare Access application for the public hostname and allow only your email or identity provider group. Add this policy before opening the domain to others. Public signup remains disabled, and only the configured admin account can access `/admin` and the admin APIs.
