#!/usr/bin/env node
/**
 * Traz o motor (sistema/) da oficina do Editor IA para a versão da Rafaela.
 *
 *   node scripts/sincronizar.mjs ["D:/Meu/Produto 3 - Edicao de video"]
 *
 * O motor é um só: correção feita na oficina do produto chega aqui com este comando.
 * O skill/ daqui é próprio da Rafaela (roteiro, estilos, catálogo) e não é tocado.
 *
 * A lista do que vem sai do git da oficina (versionado + novo que o .gitignore não
 * ignora), como no publicar.mjs de lá: nada de uso dos testes vem junto.
 * Depois de rodar, olhe o "git diff --stat sistema" antes do commit.
 */

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { copyFile, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OFICINA = path.resolve(process.argv[2] || "D:/Meu/Produto 3 - Edicao de video");

function morrer(problema) {
  console.error(`\n  [erro] ${problema}\n`);
  process.exit(1);
}

if (!existsSync(path.join(OFICINA, "sistema", "editar.py"))) {
  morrer(`Não achei a oficina em ${OFICINA}. Passe o caminho: node scripts/sincronizar.mjs CAMINHO`);
}

const lista = spawnSync("git", ["ls-files", "--cached", "--others", "--exclude-standard", "sistema"], {
  cwd: OFICINA,
  encoding: "utf8",
});
if (lista.status !== 0) morrer("Não consegui perguntar ao git da oficina o que está versionado.");

const arquivos = [...new Set(lista.stdout.split("\n").map((l) => l.trim()).filter(Boolean))].filter((f) =>
  existsSync(path.join(OFICINA, f)),
);
if (arquivos.length === 0) morrer("O git da oficina não devolveu arquivo nenhum em sistema/.");

// Troca o sistema/ inteiro: arquivo apagado na oficina também sai daqui.
await rm(path.join(AQUI, "sistema"), { recursive: true, force: true });
for (const f of arquivos) {
  const destino = path.join(AQUI, f);
  await mkdir(path.dirname(destino), { recursive: true });
  await copyFile(path.join(OFICINA, f), destino);
}

const commit = spawnSync("git", ["rev-parse", "--short", "HEAD"], { cwd: OFICINA, encoding: "utf8" }).stdout.trim();
console.log(`  [ok] ${arquivos.length} arquivos do sistema/ vindos da oficina (commit ${commit}).`);
console.log("  Confira com: git diff --stat sistema");
