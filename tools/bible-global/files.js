const fs = require('node:fs');
const path = require('node:path');
function safeOutput(root, directory) {
  const target = path.resolve(directory);
  let ancestor = target;
  while (!fs.existsSync(ancestor)) ancestor = path.dirname(ancestor);
  const resolved = path.join(fs.realpathSync(ancestor), path.relative(ancestor, target));
  const canonicalRoot = fs.realpathSync(root);
  for (const protectedPath of [canonicalRoot, path.join(canonicalRoot, 'src'), path.join(canonicalRoot, '.git')]) {
    const relative = path.relative(protectedPath, resolved);
    if (protectedPath === canonicalRoot ? relative === '' : relative === '' || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative))) throw Error('A saída deve ficar fora de src e .git, em uma pasta de relatórios separada.');
  }
  return resolved;
}

module.exports = { safeOutput };
