module.exports = {
  liveReload: true,
  domDiff: true,
  showAllHosts: true,
  middleware: [
    (req, res, next) => {
      // Definir MIME types corretos
      if (req.url.endsWith('.js')) {
        res.setHeader('Content-Type', 'application/javascript; charset=utf-8');
      } else if (req.url.endsWith('.css')) {
        res.setHeader('Content-Type', 'text/css; charset=utf-8');
      } else if (req.url.endsWith('.json')) {
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
      }
      next();
    }
  ]
};
