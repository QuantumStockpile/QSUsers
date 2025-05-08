## How to Use

### First time setup

#### Install `uv`

First, make sure you have `uv` installed. If not, you can install it using pip:

```bash
pip install uv
```

Alternatively, you can follow instructions from the [uv documentation](https://github.com/astral-sh/uv) for the latest install method.

#### Set up environment variables

* Set the `DATABASE_URL` environment variable. **This must be done through export or Docker `-e` flag; it cannot be used in dotfiles.**

```bash
export DATABASE_URL=asyncpg://user:password@localhost:5432/dbname
```

* Configure dotenv files in `env/` directory:

  * `api.env` – this file must exist, it contains some general info about the API.
  * `security.env.example` – use this as a template for your actual `security.env` file. Copy and rename it:

```bash
cp env/security.env.example env/security.env
```

Fill in the required secrets in `env/security.env` as needed.

### Install dependencies

Once `uv` is installed and your `env/` directory is populated:

```bash
uv add -r requirements.txt
```

### Launching the app

Start the FastAPI app using `uv`:

```bash
uv run uvicorn main:application
```

This will boot up your FastAPI server with the user microservice, which includes both auth and general user CRUD functionality.

If using Docker, remember to pass the `DATABASE_URL` explicitly:

```bash
docker run -e DATABASE_URL=asyncpg://user:password@host:port/dbname your_image_name
```

---

Ensure your machine has Python 3.9+ installed for compatibility with modern `uv` and FastAPI dependencies.
