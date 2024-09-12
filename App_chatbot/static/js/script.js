import { marked } from 'https://cdn.jsdelivr.net/npm/marked@4.0.12/lib/marked.esm.js';

const markdownText = document.getElementsByClassName("markdown-text");
const htmlContent = marked(markdownText);
document.getElementById("markdown-content").innerHTML = marked("a");