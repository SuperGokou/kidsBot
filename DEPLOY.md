# Deploying KidBot to Render.com

This guide walks you through deploying KidBot to Render.com with both backend API and frontend static site.

## Prerequisites

1. A [Render.com](https://render.com) account
2. Your code pushed to a GitHub/GitLab repository
3. A DeepSeek API key

## Deployment Options

### Option 1: Blueprint (Recommended - One-Click Deploy)

1. Push your code to GitHub
2. In Render Dashboard, click **New** → **Blueprint**
3. Connect your repository
4. Render will read `render.yaml` and create both services
5. Set the `DEEPSEEK_API_KEY` environment variable in the backend service

### Option 2: Manual Setup

#### Step 1: Deploy Backend API

1. Go to Render Dashboard → **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `kidbot-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

4. Add Environment Variables:
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   PYTHONUNBUFFERED=1
   ```

5. Click **Create Web Service**

6. Copy your backend URL (e.g., `https://kidbot-api.onrender.com`)

#### Step 2: Deploy Frontend

1. Go to Render Dashboard → **New** → **Static Site**
2. Connect the same repository
3. Configure:
   - **Name**: `kidbot-frontend`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`

4. Add Environment Variable:
   ```
   VITE_API_URL=https://kidbot-api.onrender.com
   ```
   (Use your actual backend URL from Step 1)

5. Add Rewrite Rule:
   - **Source**: `/*`
   - **Destination**: `/index.html`
   - **Action**: `Rewrite`

6. Click **Create Static Site**

## Environment Variables Reference

### Backend (`kidbot-api`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Yes | Your DeepSeek API key |
| `PYTHONUNBUFFERED` | Yes | Set to `1` for proper logging |
| `FRONTEND_URL` | No | Frontend URL for CORS (auto-detected for Render) |
| `SMTP_SERVER` | No | Email server for daily reports |
| `SMTP_PORT` | No | Email server port (default: 587) |
| `SMTP_USER` | No | Email username |
| `SMTP_PASS` | No | Email password/app password |

### Frontend (`kidbot-frontend`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API URL |

## Post-Deployment Checklist

- [ ] Backend health check: Visit `https://kidbot-api.onrender.com/`
- [ ] API docs: Visit `https://kidbot-api.onrender.com/docs`
- [ ] Frontend loads: Visit `https://kidbot-frontend.onrender.com`
- [ ] Test voice interaction
- [ ] Test chat functionality
- [ ] Test parent registration

## Troubleshooting

### Backend won't start

1. Check build logs for dependency errors
2. Ensure `requirements.txt` is at the root level
3. Verify Python version (3.11 recommended)

### CORS errors

1. Check `FRONTEND_URL` environment variable
2. Backend automatically allows `*.onrender.com` subdomains

### Voice transcription fails

1. FFmpeg is not installed on Render's free tier
2. Consider using a cloud speech service for production

### Slow cold starts (Free tier)

- Free tier services spin down after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- Upgrade to paid tier for always-on service

## Custom Domain

1. Go to your service → **Settings** → **Custom Domain**
2. Add your domain (e.g., `kidbot.yourdomain.com`)
3. Update DNS records as instructed
4. Update `VITE_API_URL` and `FRONTEND_URL` if using custom domains

## Monitoring

- View logs: Service → **Logs**
- View metrics: Service → **Metrics**
- Set up alerts: Service → **Settings** → **Alerts**

## Cost Estimate

| Service | Free Tier | Starter ($7/mo) |
|---------|-----------|-----------------|
| Backend | 750 hours/mo, sleeps after 15min | Always on |
| Frontend | Unlimited | Unlimited |
| Bandwidth | 100 GB/mo | 100 GB/mo |

For production use, the Starter plan is recommended to avoid cold start delays.
