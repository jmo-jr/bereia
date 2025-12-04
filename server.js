#!/usr/bin/env node
/**
 * Servidor customizado para o Eleventy com MIME types corretos
 * Usa apenas módulos nativos do Node.js
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 8080;
const SITE_DIR = path.join(__dirname, '_site');

// Mapa de tipos MIME
const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.woff': 'application/font-woff',
  '.woff2': 'application/font-woff2',
  '.ttf': 'application/font-ttf',
  '.eot': 'application/vnd.ms-fontobject',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
  // Parse the URL
  const parsedUrl = url.parse(req.url, true);
  let pathname = parsedUrl.pathname;
  
  // Remover pathprefix se existir
  if (pathname.startsWith('/bereia/')) {
    pathname = pathname.slice(7);
  }
  
  // Caminho do arquivo
  let filepath = path.join(SITE_DIR, pathname);
  
  // Se for um diretório, tenta index.html
  if (pathname.endsWith('/') || pathname === '') {
    filepath = path.join(SITE_DIR, pathname, 'index.html');
  }
  
  // Segurança: evitar directory traversal
  if (!filepath.startsWith(SITE_DIR)) {
    res.statusCode = 403;
    res.end('Forbidden');
    return;
  }
  
  fs.stat(filepath, (err, stats) => {
    if (err) {
      // Tenta index.html se for um diretório
      const indexPath = path.join(filepath, 'index.html');
      fs.readFile(indexPath, (err, data) => {
        if (err) {
          res.statusCode = 404;
          res.setHeader('Content-Type', 'text/html; charset=utf-8');
          res.end('<h1>404 - Não encontrado</h1>');
          return;
        }
        res.statusCode = 200;
        res.setHeader('Content-Type', mimeTypes['.html']);
        res.end(data);
      });
      return;
    }
    
    if (stats.isDirectory()) {
      const indexPath = path.join(filepath, 'index.html');
      fs.readFile(indexPath, (err, data) => {
        if (err) {
          res.statusCode = 404;
          res.setHeader('Content-Type', 'text/html; charset=utf-8');
          res.end('<h1>404 - Não encontrado</h1>');
          return;
        }
        res.statusCode = 200;
        res.setHeader('Content-Type', mimeTypes['.html']);
        res.end(data);
      });
      return;
    }
    
    // Obter extensão do arquivo
    const ext = path.extname(filepath).toLowerCase();
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    
    res.statusCode = 200;
    res.setHeader('Content-Type', contentType);
    fs.createReadStream(filepath).pipe(res);
  });
});

server.listen(PORT, () => {
  console.log(`\n✨ Servidor rodando em:`);
  console.log(`   http://localhost:${PORT}`);
  console.log(`   http://127.0.0.1:${PORT}`);
  console.log(`\n📁 Servindo arquivos de: ${SITE_DIR}`);
  console.log(`\nPressione Ctrl+C para parar\n`);
});

