# 🧩 React Pause UI

A lightweight **React + TypeScript** frontend built for the **Airflow-Xtra** plugin system.  
This project provides the static UI bundle for the *Bulk Pause / Unpause* feature in Airflow.

---

## ⚙️ Prerequisites

Make sure you have:
- Node.js (≥ 18.x)
- npm (≥ 9.x) or yarn

---

## 🚀 Setup

```bash
mkdir react-pause-ui
cd react-pause-ui
npm init -y
npm i -D esbuild typescript react react-dom @types/react @types/react-dom
```

---

## 🧱 Project Structure

```
react-pause-ui/
├── package.json
├── tsconfig.json
├── src/
│   └── app.tsx          # main React entry
└── public/
    ├── index.html
    └── pause-app.js     # output after build
```

---

## 🧪 Development

You can test locally by bundling and serving the static assets.

### Option A — Auto-watch for changes

```bash
npx esbuild src/app.tsx --bundle --format=iife --outfile=public/pause-app.js --watch
```

In another terminal, start a local server:

```bash
npx http-server public -p 5173
```
or
```bash
python3 -m http.server 5173 -d public
```

Then open [http://localhost:5173](http://localhost:5173) to view your UI.

---

## 🧰 Build for Airflow

To bundle and minify for production inside Airflow’s `static/` folder:

```bash
npx esbuild src/app.tsx --bundle --minify --format=iife   --outfile="pause-app.js"
```

This creates a single optimized JavaScript file (`pause-app.js`) that Airflow can serve directly.

---

## 🧩 Integration with Airflow Plugin

After building, copy or link your `pause-app.js` and `index.html` into your plugin’s `static/` directory:

```
plugins/
└── airflow_tools_ui/
    ├── airflow_tools_ui.py
    └── static/
        ├── index.html
        └── pause-app.js
```

Airflow will serve the UI at:

```
http://<host>:8080/api/airflow-tools-ui/static/index.html
```

---

## 🧾 License

MIT © [Rahul Rajasekharan](https://github.com/rahulrajasekharan)
