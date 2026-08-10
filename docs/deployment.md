# Nextstop - Deployment Guide (Railway)

This guide walks you through deploying the Nextstop (Dubai AI Travel Planner) application to [Railway.app](https://railway.app/). Railway is chosen because it easily supports deploying Docker containers and managed databases (PostgreSQL, Redis) within a single project environment.

## Prerequisites

1. A [Railway account](https://railway.app/).
2. A [GitHub account](https://github.com/) with this repository pushed to it.
3. Your API Keys:
   - `GROQ_API_KEY` (for Groq Whisper, Llama 3)
   - `GEMINI_API_KEY` (for Gemini Review Agent)

## Deployment Steps

### 1. Create a New Project on Railway
1. Go to your Railway Dashboard.
2. Click **New Project**.
3. Select **Deploy from GitHub repo**.
4. Select your `dubai-travel-planner` repository.
5. Railway will automatically detect the `Dockerfile` at the root of the repository and begin building the service.

### 2. Provision Databases (Optional)
The app is built to automatically fall back to a local SQLite database and file-based caching if no external databases are provided. If you want persistent data across server restarts, you can add PostgreSQL and Redis:
1. In your Railway project view, click the **New** button (Note: Services are added to your *current* project, they do not consume additional projects).
2. Select **Database** -> **Add PostgreSQL**.
3. Once provisioned, click **New** again.
4. Select **Database** -> **Add Redis**.

*If you are on the free tier or want a simpler setup, you can completely skip this step! The app will run perfectly using a single service.*

### 3. Configure Environment Variables
Now we must inject the necessary environment variables into the main API service.
1. Click on your main API service (the one built from your GitHub repo).
2. Go to the **Variables** tab.
3. Add the following variables:
   - `GROQ_API_KEY`: `<your_groq_api_key>`
   - `GROQ_MODEL`: `llama-3.3-70b-versatile`
   - `GEMINI_API_KEY`: `<your_gemini_api_key>`
   - `GEMINI_MODEL`: `gemini-2.5-flash`
   
4. Link the databases to the app:
   - For `DATABASE_URL`: Click the **Reference Variable** button (or type `${{}}`), select the PostgreSQL service, and pick its `DATABASE_URL` (this will automatically inject the connection string).
   - For `REDIS_URL`: Click **Reference Variable**, select the Redis service, and pick its `REDIS_URL`.

5. *Optional*: Adjust `API_PORT` if needed (Railway will dynamically provide a `$PORT` variable, so FastAPI and Uvicorn should be able to bind to `0.0.0.0:$PORT`. The current Dockerfile binds to `8000`, so make sure `PORT=8000` is set in the variables if Railway doesn't override the `CMD` automatically).

### 4. Expose to the Public Internet
By default, Railway services are private.
1. Click on your API service.
2. Go to the **Settings** tab.
3. Scroll down to **Networking**.
4. Click **Generate Domain**. Railway will assign a `.up.railway.app` URL to your project.

### 5. Verify the Deployment
1. Wait for the build and deployment pipeline to finish.
2. Click on the generated public URL. You should see the `index.html` frontend load!
3. Add `/docs` to the end of your public URL to test the FastAPI Swagger documentation.

## Troubleshooting
- **Database Connection Issues:** Ensure `asyncpg` is installed (it is in the `pyproject.toml` under the `db` extra). Ensure the URL starts with `postgresql+asyncpg://`. Railway's default variable might just be `postgresql://`. If so, you will need to manually format the `DATABASE_URL` string in the variables to include `+asyncpg`.
- **Audio Uploads Failing:** Make sure the Nginx proxy in front of Railway allows large payloads (Railway defaults are usually sufficient for voice notes).
- **Timeouts:** Groq and Gemini APIs generally return responses within 10-20 seconds. If they timeout, the FastAPI endpoint may hit Railway's maximum request timeout limit (typically 100 seconds).

---
*Happy Deploying!*
