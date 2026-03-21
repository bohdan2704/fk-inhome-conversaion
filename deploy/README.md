# VPS Docker Autodeploy

This repo is now prepared for Docker-based autodeploy to a VPS:

1. GitHub Actions validates Python and Docker files on every push to `main`.
2. The workflow syncs the repo to your VPS over SSH with `rsync`.
3. The VPS runs `deploy/remote_deploy.sh`.
4. The script creates the shared runtime folders and runs `docker compose up -d --build`.

## 1. First-time VPS setup

These steps match your current access style: `root@194.31.52.91`.

Log into the server:

```bash
ssh -i ~/.ssh/github_actions_vps root@194.31.52.91
```

Install Docker and rsync:

```bash
apt update
apt install -y docker.io docker-compose-v2 rsync
systemctl enable docker
systemctl start docker
```

Open the HTTP and HTTPS ports in the VPS firewall if they are blocked:

```bash
ufw allow 80/tcp
ufw allow 443/tcp
```

If `ufw` is not installed, make the equivalent change in your VPS provider firewall panel.

Create the app and shared directories:

```bash
mkdir -p /srv/convert-api/app
mkdir -p /srv/convert-api/shared
mkdir -p /srv/convert-api/shared/logs
mkdir -p /srv/convert-api/shared/generated
```

If you deploy as `root`, that is enough. If later you switch to a non-root deploy user, that user must own `/srv/convert-api`.

## 2. GitHub secrets

Add these repository secrets:

- `VPS_HOST`: `194.31.52.91`
- `VPS_PORT`: `22`
- `VPS_USER`: `root`
- `VPS_SSH_KEY`: the private key you already added
- `DEPLOY_PATH`: `/srv/convert-api/app`

The matching public SSH key must be present in `/root/.ssh/authorized_keys` because `VPS_USER=root`.

## 3. DNS for fk-inhome.space

At your DNS provider, point the domain to the VPS:

- `A` record for `fk-inhome.space` -> `194.31.52.91`
- optional `CNAME` for `www` -> `fk-inhome.space`

Important:

- If you already have an `AAAA` record for `fk-inhome.space`, either point it to your VPS IPv6 or remove it for now.
- Automatic HTTPS will not work correctly if the domain resolves somewhere else.

## 4. First deploy

After the first push to `main`, GitHub Actions will copy the repo into:

```text
/srv/convert-api/app
```

The remote deploy script will also create this file automatically if it does not exist:

```text
/srv/convert-api/shared/convert-api.env
```

It is copied from:

```text
deploy/env/convert-api.env.example
```

Because the API runs inside Docker, paths in that env file must be container paths, not VPS host paths. The correct source paths are:

```text
FEED_SOURCE_PATH=/app/feed_module/xml_example/fk-inhome.com.ua.xml
FEED_SUPPLEMENTAL_SOURCE_PATH=/app/feed_module/xml_example/fk-inhome.com.ua=2.xml
```

The Docker stack now includes Caddy for automatic HTTPS with:

```text
https://fk-inhome.space
https://www.fk-inhome.space
```

If you want to change the port or source feed paths later, edit:

```text
/srv/convert-api/shared/convert-api.env
```

## 5. Verify on the VPS

After GitHub Actions runs, check:

```bash
cd /srv/convert-api/app
docker compose ps
docker compose logs --tail=100
```

The API should be reachable by domain:

```text
https://fk-inhome.space/api/content-feed.xml
https://fk-inhome.space/api/propositions-feed.xml
```

You can still test the backend locally on the VPS:

```bash
curl http://127.0.0.1:8000/api/content-feed.xml | head
curl http://127.0.0.1:8000/api/propositions-feed.xml | head
```

If the certificate is still being issued, watch:

```bash
docker compose logs -f caddy
```

## 6. Domain config in repo

The active HTTPS routing file is:

```text
deploy/Caddyfile
```

It currently serves:

- `fk-inhome.space`
- `www.fk-inhome.space` -> redirected to `fk-inhome.space`

## 7. Deploy flow

After this setup, every push to `main` triggers:

- syntax validation in GitHub Actions
- file sync to the VPS
- Docker rebuild on the VPS
- `docker compose up -d --build`
