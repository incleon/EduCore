# EduCore deployment guide

After analyzing the application stack (FastAPI Backend, React/Vite Frontend, MySQL Database) and the existing infrastructure configuration (`docker-compose.yml`), this document outlines the best deployment platforms and provides a step-by-step guide to get the CMS live.

## 📊 Platform Analysis & Recommendation

The presence of a fully configured `docker-compose.yml` file significantly simplifies deployment. We evaluated three deployment approaches:

1. **Virtual Private Server (VPS) - e.g., DigitalOcean, AWS EC2, Hetzner, Linode**
   - **Pros:** Most cost-effective. Leverages your existing `docker-compose.yml` natively. Full control over the server environment.
   - **Cons:** Requires manual initial setup (installing Docker, setting up SSL).
   - **Verdict:** ⭐ **BEST OVERALL FIT**. It directly uses your current Docker architecture without needing code/config splits.

2. **Platform as a Service (PaaS) - e.g., Render, Railway, Heroku**
   - **Pros:** Zero infrastructure management. Built-in CI/CD (auto-deploys on git push). Built-in SSL.
   - **Cons:** You cannot use `docker-compose` directly. You must deploy MySQL, FastAPI, and React as three separate managed services. More expensive at scale.
   - **Verdict:** Great alternative if you want zero server management, but requires splitting your current monolithic docker setup.

3. **Cloud Native - e.g., AWS ECS/EKS + RDS + S3/CloudFront**
   - **Pros:** Enterprise-grade scalability, high availability.
   - **Cons:** High complexity, steep learning curve, higher baseline costs.
   - **Verdict:** Overkill for the initial launch, but a viable migration path for the future.

---

## 🏆 Primary Recommendation: VPS (DigitalOcean Droplet or AWS EC2)

Because you already have a functional Docker Compose setup, deploying on a Linux VPS (Ubuntu 24.04/22.04 LTS) is the most efficient method. 

### Step-by-Step Deployment Instructions

#### Step 1: Provision the Server
1. Create an account on **DigitalOcean** (or AWS, Hetzner, etc.).
2. Create a new "Droplet" (Virtual Machine).
3. Select **Ubuntu 24.04 (LTS) x64** as the OS.
4. Choose a size: A minimum of **2GB RAM / 1 vCPU** is recommended because you are running MySQL, Python, and Node inside containers.
5. Add your SSH keys for secure access.
6. Create the Droplet and note its public IP address.

#### Step 2: Initial Server Setup
SSH into your new server:
```bash
ssh root@YOUR_SERVER_IP
```

Update packages and install **Docker** and **Docker Compose**:
```bash
# Update system
apt update && apt upgrade -y

# Install prerequisites
apt install apt-transport-https ca-certificates curl software-properties-common git -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify Docker installation
docker --version
docker compose version
```

#### Step 3: Clone Repository & Configure Environment
Clone your project repository onto the server:
```bash
git clone https://github.com/your-username/EduCoreV2.git /opt/cms
cd /opt/cms
```

Set up the production environment variables:
```bash
cp backend/.env.example backend/.env
nano backend/.env
```
*Make sure to change `DEBUG=False` and update `DATABASE_URL` with secure passwords matching your `docker-compose.yml`.*

#### Step 4: Build and Run Containers
With Docker installed and the repository cloned, run the application:
```bash
# Build the images and start the containers in detached mode
docker compose up -d --build

# Verify that all 3 containers (db, backend, frontend) are running
docker ps
```
Your frontend is now exposed on port `8080`, backend on `8000`, and DB on `3306` (per your docker-compose file).

#### Step 5: Production Reverse Proxy & SSL (Nginx & Certbot)
Exposing raw ports is not recommended for production. You should set up a reverse proxy with Nginx to map your domains (e.g., `cms.yourdomain.com`) to the Docker containers and secure them with HTTPS.

1. **Install Nginx and Certbot:**
   ```bash
   apt install nginx certbot python3-certbot-nginx -y
   ```
2. **Configure Nginx (`/etc/nginx/sites-available/cms`):**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;

       # Route to Frontend (Vite/Nginx Container)
       location / {
           proxy_pass http://localhost:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }

       # Route to Backend API
       location /api/ {
           proxy_pass http://localhost:8000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```
3. **Enable the site and obtain SSL Certificate:**
   ```bash
   ln -s /etc/nginx/sites-available/cms /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx

   # Obtain free SSL certificate from Let's Encrypt
   certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

---

## 🥈 Alternative Recommendation: Render or Railway (PaaS)

If you prefer to avoid the terminal and server maintenance, use a PaaS. You will deploy the stack as three separate pieces.

### Step 1: Deploy MySQL Database
1. Go to the Railway/Render dashboard and provision a **MySQL** database.
2. Note the generated connection credentials (`Host`, `Port`, `User`, `Password`).

### Step 2: Deploy FastAPI Backend
1. Create a new **Web Service** linked to your GitHub repo.
2. Set the Root Directory to `backend/`.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python run.py` (or uvicorn equivalent based on your backend structure).
5. Add Environment Variables: Add `DATABASE_URL` pointing to the MySQL database created in Step 1.

### Step 3: Deploy React Frontend
1. Create a new **Static Site** linked to your GitHub repo.
2. Set the Root Directory to `frontend/`.
3. Build Command: `npm install && npm run build`
4. Publish Directory: `frontend/dist`
5. Configure Rewrites to handle React Router: Rewrite `/*` to `/index.html`.
6. Add Environment Variable: Set `VITE_API_URL` to point to the backend service URL from Step 2.

---

## 💸 Free Deployment Alternatives (Zero Cost Setup)

If you are looking for a completely free setup for a proof-of-concept or hobby project, you can stitch together several free-tier services. Note that free tiers often come with limitations (e.g., sleeping containers, limited bandwidth, or database storage caps).

### Step 1: Free MySQL Database
- **Aiven**: Offers a free tier for MySQL with 5GB of storage.
- **TiDB Serverless**: Offers a generous free tier for MySQL-compatible databases.
- *Action*: Provision the database and obtain your `DATABASE_URL`.

### Step 2: Free FastAPI Backend
- **Render (Free Web Service)**: You can deploy your FastAPI backend here. Note that the free tier spins down after 15 minutes of inactivity, causing a ~50-second cold start on the next request.
- **Koyeb**: Offers a free tier with "eco" instances that are great for Dockerized APIs or Python services.
- *Action*: Connect your GitHub repo, set the build/start commands, and inject the `DATABASE_URL` from Step 1.

### Step 3: Free React Frontend
- **Vercel** or **Netlify**: Both offer excellent, fast, and completely free hosting for static sites and frontend frameworks.
- *Action*: Connect your repository, set the root directory to `frontend/`, configure the build command (`npm run build`), and set `VITE_API_URL` to your backend's URL.

---

## 🔄 Updating the Application (Post-Deployment)

### For VPS (Docker Compose) Workflow:
When you make changes to the code and push to GitHub, SSH into your server and run:
```bash
cd /opt/cms
git pull origin main
docker compose up -d --build
```

### For PaaS Workflow:
Just push to the `main` branch on GitHub. The PaaS will automatically detect the changes, pull the code, build, and deploy with zero downtime.
