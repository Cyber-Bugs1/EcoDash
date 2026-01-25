# Static URL Options for Local Server Exposure

Since you asked about making the link static, here are the two main options available for free.

## Option 1: Cloudflare Tunnel (Recommended for Speed)
By default, Cloudflare Quick Tunnels (what we are using) generate a random URL (e.g., `https://random-name.trycloudflare.com`).

**To get a static URL (e.g., `https://api.myproject.com`):**
1.  **You must own a domain name** (e.g., from Namecheap, GoDaddy, or a free .tk one).
2.  **Create a Cloudflare Account** (Free).
3.  **Add your domain** to Cloudflare.
4.  **Login** locally:
    ```powershell
    .\scripts\cloudflared.exe login
    ```
5.  **Create a named tunnel**:
    ```powershell
    .\scripts\cloudflared.exe tunnel create satalite-tunnel
    .\scripts\cloudflared.exe tunnel route dns satalite-tunnel api.myproject.com
    .\scripts\cloudflared.exe tunnel run satalite-tunnel
    ```

**Pros:** Low latency, no connection limits.
**Cons:** Requires owning a domain.

## Option 2: Ngrok (Recommended for Static URL without Domain)
Ngrok now offers **1 free static domain** for all free accounts.

**To get a static URL (e.g., `https://cool-name.ngrok-free.app`):**
1.  Go to the [Ngrok Dashboard](https://dashboard.ngrok.com/cloud-edge/domains).
2.  Claim your free static domain.
3.  Update the start script to use this domain.

**Pros:** easy static URL, no custom domain needed.
**Cons:** Higher latency than Cloudflare, connection limits.
