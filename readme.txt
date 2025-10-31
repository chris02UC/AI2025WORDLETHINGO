1. Library yang Digunakan
- Dari Python (Library Standar) -> random, math, time, re, threading, tkinter

- Dari eksternal -> matplotlib, numpy

2. IDE yang Digunakan
 -> Jupyter Notebook versi 7.2.2; Python versi 3.12
 -> VSCode versi 1.105.1

untuk menjalankan, tipe IDE lebih penting daripada versi, oleh karena itu kami menyarankan untuk menggunakan Jupyter Notebook karena lebih user-friendly. Untuk langkah instalasi, kita menyarankan menggunakan Terminal/CMD.

3.a Langkah - Langkah Instalasi & Menjalankan (Terminal/CMD)
	1. Pastikan 5 file proyek (main.py, gui.py, RunWordleAI.ipynb, words.txt, wordsAllowed.txt) sudah Anda extract ke dalam satu folder.
	2. Install semua library eksternal yang dibutuhkan dengan menjalankan perintah berikut: pip install matplotlib numpy notebook
	3. Setelah instalasi, di CMD/Powershell (Windows) atau Terminal (macOS/Linux), gunakan perintah cd untuk pindah direktori ke tempat Anda menyimpan 5 file proyek; misalnya: cd C:\Users\NamaAnda\Documents\AI2025WORDLETHINGO
	4. Untuk Windows, jalankan file gui.py menggunakan perintah: python gui.py ; Untuk macOS/Linux, jalankan file gui.py menggunakan perintah: python3 gui.py
	5. Selamat bermain!!!

3.b Langkah - Langkah Instalasi & Menjalankan (Jupyter Notebook)
	1. Installasi Jupyter Notebook: buka link ini di browser https://jupyter.org/install; lalu ikuti langkah - langkah untuk menginstal Jupyter Notebook
	2. Download source file (.zip) dari kami, lalu extract di direktori yang sama / di bawah dari program Jupyter Notebook. Jika tidak menemukan folder source file yang telah di extract, bisa menuju ke file -> new -> terminal -> cd <direktori folder> -> ketik jupyter notebook -> tekan Enter.
	3. Pastikan bahwa seluruh file berikut di dalam satu folder yang ter-extract:
    - main.py
    - gui.py
    - RunWordleAI.ipynb
    - words.txt
    - wordsAllowed.txt
	4. Untuk menjalankan game, bisa ke file -> new -> terminal -> ketik python gui.py -> klik Enter
	5. Selamat bermain!!!