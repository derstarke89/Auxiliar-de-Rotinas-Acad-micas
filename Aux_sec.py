import customtkinter as ctk
import calendar
from datetime import datetime
import json
import os
import shutil
from tkinter import filedialog, messagebox

# --- VERSÃO 1.21 (Modificada para Persistência em Executável) ---
# Desenvolvido por RAM

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GestorTrabalhoRAM(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CONFIGURAÇÃO DE DIRETÓRIOS (CORREÇÃO PARA EXECUTÁVEL) ---
        self.diretorio_app = os.path.join(os.environ['APPDATA'], 'GestorTrabalhoRAM')
        if not os.path.exists(self.diretorio_app):
            os.makedirs(self.diretorio_app)
            
        self.pasta_anexos = os.path.join(self.diretorio_app, "anexos_trabalho")
        if not os.path.exists(self.pasta_anexos): 
            os.makedirs(self.pasta_anexos)
            
        self.caminho_dados = os.path.join(self.diretorio_app, "trabalho_v3.json")

        # Configurações de Cores Premium
        self.COR_FUNDO = "#1A1C1E"
        self.COR_CARD = "#2A2D31"
        self.COR_ATEND = "#0078D4"
        self.COR_RETOR = "#28A745"
        self.COR_TAREF = "#E81123"
        self.COR_TEXTO = "#E0E0E0"

        self.dados = self.carregar_dados()
        
        self.title("Gestor de Trabalho RAM - v1.21")
        self.largura, self.altura = 1380, 880
        self.centralizar_janela(self, self.largura, self.altura)
        self.configure(fg_color=self.COR_FUNDO)

        self.hoje_dt = datetime.now()
        self.ano_atual, self.mes_atual = self.hoje_dt.year, self.hoje_dt.month
        self.dia_selecionado = self.hoje_dt.strftime("%Y-%m-%d")
        self.termo_busca = ""
        self.filtro_tipo_dash = None
        self.mostrar_apenas_pendentes = False
        self.cards_expandidos = set()
        
        self.setup_ui()

    def carregar_dados(self):
        if os.path.exists(self.caminho_dados):
            try:
                with open(self.caminho_dados, 'r', encoding='utf-8') as f: return json.load(f)
            except: return {}
        return {}

    def salvar_dados(self):
        with open(self.caminho_dados, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, indent=4, ensure_ascii=False)
        self.atualizar_dash()

    def centralizar_janela(self, win, w, h):
        win.geometry(f'{w}x{h}+{(win.winfo_screenwidth()//2)-(w//2)}+{(win.winfo_screenheight()//2)-(h//2)}')

    def setup_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=3); self.grid_rowconfigure(0, weight=1)
        
        self.f_esq = ctk.CTkFrame(self, fg_color="#212529", corner_radius=0)
        self.f_esq.grid(row=0, column=0, sticky="nsew")
        
        self.f_cal_head = ctk.CTkFrame(self.f_esq, fg_color="transparent")
        self.f_cal_head.pack(fill="x", pady=(20, 10))
        ctk.CTkButton(self.f_cal_head, text="<", width=30, fg_color="#343A40", command=self.mes_ant).pack(side="left", padx=10)
        self.lbl_mes = ctk.CTkLabel(self.f_cal_head, text="", font=("Segoe UI", 16, "bold"), text_color="white")
        self.lbl_mes.pack(side="left", expand=True)
        ctk.CTkButton(self.f_cal_head, text=">", width=30, fg_color="#343A40", command=self.mes_prox).pack(side="right", padx=10)
        
        self.cont_dias = ctk.CTkFrame(self.f_esq, fg_color="transparent")
        self.cont_dias.pack(fill="x", padx=10)
        
        ctk.CTkLabel(self.f_esq, text="DASHBOARD", font=("Segoe UI", 11, "bold"), text_color="#6C757D").pack(pady=(30, 10))
        self.f_dash = ctk.CTkFrame(self.f_esq, fg_color="transparent")
        self.f_dash.pack(fill="x", padx=15)
        
        self.dash_items = {}
        icones = {"Atendimento": "📝", "Retorno": "🔔", "Tarefa": "✅"}
        cores = {"Atendimento": self.COR_ATEND, "Retorno": self.COR_RETOR, "Tarefa": self.COR_TAREF}
        
        for tipo, icone in icones.items():
            btn = ctk.CTkButton(self.f_dash, text=f"{icone}  0 {tipo}s", fg_color=cores[tipo], 
                                height=45, corner_radius=10, font=("Segoe UI", 13, "bold"), 
                                anchor="w", command=lambda t=tipo: self.set_filtro_dash(t))
            btn.pack(fill="x", pady=4)
            self.dash_items[tipo] = btn

        self.sw_pend = ctk.CTkSwitch(self.f_esq, text="Ver Tudo", font=("Segoe UI", 12), command=self.toggle_pend)
        self.sw_pend.pack(pady=20)
        
        f_db = ctk.CTkFrame(self.f_esq, fg_color="transparent")
        f_db.pack(side="bottom", pady=20)
        ctk.CTkButton(f_db, text="💾 Exportar", width=100, fg_color="#495057", command=self.exportar_dados).pack(side="left", padx=5)
        ctk.CTkButton(f_db, text="📥 Importar", width=100, fg_color="#495057", command=self.importar_dados).pack(side="left", padx=5)

        self.f_dir = ctk.CTkFrame(self, fg_color=self.COR_FUNDO, corner_radius=0)
        self.f_dir.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        f_header_main = ctk.CTkFrame(self.f_dir, fg_color="transparent")
        f_header_main.pack(fill="x", pady=(0, 20))
        
        self.lbl_dia = ctk.CTkLabel(f_header_main, text="", font=("Segoe UI", 28, "bold"), text_color="white")
        self.lbl_dia.pack(side="left")
        
        self.ent_busca = ctk.CTkEntry(f_header_main, placeholder_text="🔍 Pesquisar Global por Nome ou RA...", width=350, 
                                     height=40, corner_radius=20, border_color="#343A40", fg_color=self.COR_CARD)
        self.ent_busca.pack(side="right")
        self.ent_busca.bind("<KeyRelease>", self.filtrar)

        self.scroll = ctk.CTkScrollableFrame(self.f_dir, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True)
        
        self.f_btns = ctk.CTkFrame(self.f_dir, fg_color="transparent")
        self.f_btns.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(self.f_btns, text="+ NOVO ATENDIMENTO", fg_color=self.COR_ATEND, height=50, 
                      corner_radius=15, font=("Segoe UI", 14, "bold"), 
                      command=self.janela_atendimento).pack(side="left", expand=True, fill="x", padx=10)
                      
        ctk.CTkButton(self.f_btns, text="+ NOVA TAREFA", fg_color=self.COR_TAREF, height=50, 
                      corner_radius=15, font=("Segoe UI", 14, "bold"), 
                      command=self.janela_tarefa).pack(side="left", expand=True, fill="x", padx=10)

        ctk.CTkLabel(self.f_dir, text="Desenvolvido por RAM", font=("Segoe UI", 11), text_color="#495057").pack(pady=10)
        
        self.gerar_cal(); self.atualizar_lista(); self.atualizar_dash()

    def criar_card(self, d, h, info):
        card_id = f"{d}_{h}"
        tipo = info.get('tipo', 'Atendimento')
        cor_lateral = self.COR_ATEND if tipo == "Atendimento" else (self.COR_RETOR if tipo == "Retorno" else self.COR_TAREF)
        
        card = ctk.CTkFrame(self.scroll, fg_color=self.COR_CARD, corner_radius=12, border_width=0)
        card.pack(fill="x", pady=6, padx=5)
        f_ind = ctk.CTkFrame(card, width=6, fg_color=cor_lateral, corner_radius=0)
        f_ind.pack(side="left", fill="y")
        
        f_header = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        f_header.pack(fill="x", padx=15, pady=10)
        f_header.bind("<Button-1>", lambda e: self.toggle_card(card_id))
        
        exibir_data_crucial = self.termo_busca or self.mostrar_apenas_pendentes
        tag_data = ""
        
        if exibir_data_crucial:
            data_formatada = f"{d[8:10]}/{d[5:7]}" # DD/MM
            if tipo == "Retorno":
                tag_data = f" [📅 Retorno: {data_formatada}]"
            elif tipo == "Tarefa":
                tag_data = f" [🕒 Prazo: {info.get('limite', 'S/D')}]"
            else:
                tag_data = f" [{data_formatada}]"

        txt_titulo = f"{h}{tag_data}  •  {info['nome']}"
        
        lbl_titulo = ctk.CTkLabel(f_header, text=txt_titulo, font=("Segoe UI", 14, "bold"), text_color="white")
        lbl_titulo.pack(side="left")
        lbl_titulo.bind("<Button-1>", lambda e: self.toggle_card(card_id))
        
        cb = ctk.CTkCheckBox(f_header, text="Concluído", font=("Segoe UI", 12), border_color=cor_lateral, 
                             hover_color=cor_lateral, command=lambda: self.toggle_concluido(d, h))
        cb.pack(side="right")
        cb.select() if info.get("concluido") else None

        if card_id in self.cards_expandidos:
            f_body = ctk.CTkFrame(card, fg_color="transparent")
            f_body.pack(fill="x", padx=20, pady=(0, 15))
            texto_detalhes = f"🆔 RA: {info.get('ra','-')}   |   📞 Contato: {info.get('contato','-')}"
            ctk.CTkLabel(f_body, text=texto_detalhes, font=("Segoe UI", 12), text_color="#ADB5BD").pack(anchor="w", pady=5)
            t_area = ctk.CTkTextbox(f_body, height=100, fg_color="#1A1C1E", border_color="#343A40", corner_radius=8, font=("Segoe UI", 12))
            t_area.pack(fill="x", pady=5); t_area.insert("0.0", info.get("anotacoes",""))
            f_anexos = ctk.CTkFrame(f_body, fg_color="transparent")
            f_anexos.pack(fill="x", pady=5)
            for arq_rel in info.get("arquivos", []):
                arq_abs = os.path.join(self.diretorio_app, arq_rel)
                fa = ctk.CTkFrame(f_anexos, fg_color="#343A40", corner_radius=6)
                fa.pack(fill="x", pady=2)
                ctk.CTkLabel(fa, text=f"📎 {os.path.basename(arq_rel)}", font=("Segoe UI", 11)).pack(side="left", padx=10)
                ctk.CTkButton(fa, text="ABRIR", width=60, height=20, fg_color="#495057", command=lambda p=arq_abs: os.startfile(p)).pack(side="right", padx=5)
            f_actions = ctk.CTkFrame(f_body, fg_color="transparent")
            f_actions.pack(fill="x", pady=(10, 0))
            ctk.CTkButton(f_actions, text="+ Anexar Arquivo", width=120, height=28, fg_color="#343A40", font=("Segoe UI", 11), command=lambda: self.anexar(d, h)).pack(side="left")
            ctk.CTkButton(f_actions, text="Salvar Alterações", width=130, height=28, fg_color=self.COR_RETOR, font=("Segoe UI", 11, "bold"), command=lambda: self.salvar_nota(d, h, t_area)).pack(side="right")

    def exportar_dados(self):
        self.attributes("-topmost", False); destino = filedialog.asksaveasfilename(defaultextension=".json"); self.attributes("-topmost", True)
        if destino:
            with open(destino, 'w', encoding='utf-8') as f: json.dump(self.dados, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("RAM", "Exportado!")

    def importar_dados(self):
        self.attributes("-topmost", False); origem = filedialog.askopenfilename(); self.attributes("-topmost", True)
        if origem and messagebox.askyesno("RAM", "Substituir dados atuais?"):
            with open(origem, 'r', encoding='utf-8') as f: self.dados = json.load(f)
            self.salvar_dados(); self.atualizar_lista(); self.gerar_cal()

    def atualizar_dash(self):
        counts = {"Atendimento": 0, "Retorno": 0, "Tarefa": 0}
        for dia in self.dados.values():
            for info in dia.values():
                t = info.get("tipo")
                if not info.get("concluido") and t in counts: counts[t] += 1
        icones = {"Atendimento": "📝", "Retorno": "🔔", "Tarefa": "✅"}
        for tipo, btn in self.dash_items.items(): btn.configure(text=f"{icones[tipo]}  {counts[tipo]} {tipo}s")

    def set_filtro_dash(self, tipo):
        self.filtro_tipo_dash = tipo; self.mostrar_apenas_pendentes = True
        self.sw_pend.select(); self.ent_busca.delete(0, 'end'); self.termo_busca = ""
        self.atualizar_lista()

    def janela_atendimento(self):
        j = ctk.CTkToplevel(self); self.centralizar_janela(j, 450, 700); j.title("Registro"); j.attributes("-topmost", True); j.grab_set()
        ctk.CTkLabel(j, text="Nome:").pack(pady=(15,0)); en = ctk.CTkEntry(j, width=350); en.pack()
        ctk.CTkLabel(j, text="RA:").pack(); er = ctk.CTkEntry(j, width=200); er.pack()
        ctk.CTkLabel(j, text="Contato:").pack(); ec = ctk.CTkEntry(j, width=350); ec.pack()
        f_dt = ctk.CTkFrame(j, fg_color="transparent"); f_dt.pack(pady=10)
        ed = ctk.CTkEntry(f_dt, width=100); ed.insert(0, datetime.now().strftime("%d/%m/%Y")); ed.grid(row=0, column=0, padx=5)
        eh = ctk.CTkEntry(f_dt, width=80); eh.insert(0, datetime.now().strftime("%H:%M")); eh.grid(row=0, column=1)
        ctk.CTkLabel(j, text="Notas:").pack(); ta = ctk.CTkTextbox(j, width=350, height=80); ta.pack()
        f_ret = ctk.CTkFrame(j, fg_color="#2A2D31"); f_ret.pack(pady=15, fill="x", padx=40)
        var_ret = ctk.BooleanVar(); er_dt = ctk.CTkEntry(f_ret, width=120, state="disabled")
        def toggle(): er_dt.configure(state="normal" if var_ret.get() else "disabled")
        ctk.CTkCheckBox(f_ret, text="Agendar Retorno?", variable=var_ret, command=toggle).pack(side="left", padx=10); er_dt.pack(side="left", padx=10)
        def salvar():
            try:
                dt_key = datetime.strptime(ed.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
                if dt_key not in self.dados: self.dados[dt_key] = {}
                self.dados[dt_key][eh.get()] = {"tipo": "Atendimento", "nome": en.get(), "ra": er.get(), "contato": ec.get(), "anotacoes": ta.get("0.0", "end-1c"), "concluido": False, "arquivos": []}
                if var_ret.get():
                    dt_r = datetime.strptime(er_dt.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
                    if dt_r not in self.dados: self.dados[dt_r] = {}
                    self.dados[dt_r][f"{eh.get()} (RET)"] = {"tipo": "Retorno", "nome": f"RETORNO: {en.get()}", "ra": er.get(), "contato": ec.get(), "anotacoes": "Retorno agendado", "concluido": False, "arquivos": []}
                self.salvar_dados(); self.atualizar_lista(); j.destroy()
            except: messagebox.showerror("Erro", "Data inválida")
        ctk.CTkButton(j, text="SALVAR", fg_color=self.COR_ATEND, height=40, command=salvar).pack(pady=10)

    def janela_tarefa(self):
        j = ctk.CTkToplevel(self); self.centralizar_janela(j, 450, 500); j.title("Tarefa"); j.attributes("-topmost", True); j.grab_set()
        ctk.CTkLabel(j, text="Nome:").pack(pady=10); en = ctk.CTkEntry(j, width=350); en.pack()
        ctk.CTkLabel(j, text="Limite:").pack(); el = ctk.CTkEntry(j, width=150); el.pack()
        ctk.CTkLabel(j, text="Anotações:").pack(); ta = ctk.CTkTextbox(j, width=350, height=100); ta.pack()
        def salvar():
            d = self.dia_selecionado
            if d not in self.dados: self.dados[d] = {}
            self.dados[d][datetime.now().strftime("%H:%M:%S")] = {"tipo": "Tarefa", "nome": en.get(), "limite": el.get(), "anotacoes": ta.get("0.0", "end-1c"), "concluido": False, "arquivos": []}
            self.salvar_dados(); self.atualizar_lista(); j.destroy()
        ctk.CTkButton(j, text="GRAVAR", fg_color=self.COR_TAREF, command=salvar).pack(pady=20)

    def atualizar_lista(self):
        for w in self.scroll.winfo_children(): w.destroy()
        exibir = []
        if self.termo_busca:
            self.lbl_dia.configure(text=f"BUSCA: '{self.termo_busca.upper()}'")
            for d, hs in self.dados.items():
                for h, info in hs.items():
                    if self.termo_busca in info.get('nome','').lower() or self.termo_busca in info.get('ra',''):
                        exibir.append((d, h, info))
            exibir.sort(key=lambda x: x[0], reverse=True)
        elif self.mostrar_apenas_pendentes:
            self.lbl_dia.configure(text=f"PENDÊNCIAS GERAIS {f'({self.filtro_tipo_dash})' if self.filtro_tipo_dash else ''}")
            for d, hs in self.dados.items():
                for h, info in hs.items():
                    if not info.get("concluido"):
                        if self.filtro_tipo_dash and info['tipo'] != self.filtro_tipo_dash: continue
                        exibir.append((d, h, info))
            exibir.sort(key=lambda x: x[0])
        else:
            dt_f = datetime.strptime(self.dia_selecionado, "%Y-%m-%d").strftime("%d/%m/%Y")
            self.lbl_dia.configure(text=dt_f)
            if self.dia_selecionado in self.dados:
                for h in sorted(self.dados[self.dia_selecionado].keys()): 
                    exibir.append((self.dia_selecionado, h, self.dados[self.dia_selecionado][h]))
        for d, h, info in exibir:
            self.criar_card(d, h, info)

    def toggle_card(self, card_id):
        if card_id in self.cards_expandidos: self.cards_expandidos.remove(card_id)
        else: self.cards_expandidos.add(card_id)
        self.atualizar_lista()

    def anexar(self, d, h):
        self.attributes("-topmost", False); paths = filedialog.askopenfilenames(); self.attributes("-topmost", True)
        if paths:
            for p in paths:
                nome = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(p)}"
                shutil.copy2(p, os.path.join(self.pasta_anexos, nome))
                caminho_relativo = os.path.join("anexos_trabalho", nome)
                self.dados[d][h]["arquivos"].append(caminho_relativo)
            self.salvar_dados(); self.atualizar_lista()

    def salvar_nota(self, d, h, t):
        self.dados[d][h]["anotacoes"] = t.get("0.0", "end-1c"); self.salvar_dados(); messagebox.showinfo("RAM", "Salvo!")

    def toggle_concluido(self, d, h):
        self.dados[d][h]["concluido"] = not self.dados[d][h].get("concluido", False)
        self.salvar_dados(); self.atualizar_lista(); self.gerar_cal()

    def gerar_cal(self):
        for w in self.cont_dias.winfo_children(): w.destroy()
        for i, d in enumerate(["S","T","Q","Q","S","S","D"]): ctk.CTkLabel(self.cont_dias, text=d, font=("Segoe UI", 10, "bold"), text_color="#6C757D").grid(row=0, column=i)
        cal = calendar.monthcalendar(self.ano_atual, self.mes_atual)
        for r, sem in enumerate(cal):
            for c, dia in enumerate(sem):
                if dia != 0:
                    dt_iso = f"{self.ano_atual}-{self.mes_atual:02d}-{dia:02d}"
                    cor = "#212529"
                    if dt_iso in self.dados and self.dados[dt_iso]:
                        cor = self.COR_RETOR if all(v.get("concluido") for v in self.dados[dt_iso].values()) else self.COR_ATEND
                    if dt_iso == self.dia_selecionado: cor = "#6C757D"
                    ctk.CTkButton(self.cont_dias, text=str(dia), width=35, height=35, fg_color=cor, corner_radius=6, command=lambda d1=dt_iso: self.clicar_dia(d1)).grid(row=r+1, column=c, padx=2, pady=2)
        self.lbl_mes.configure(text=f"{calendar.month_name[self.mes_atual]} {self.ano_atual}")

    def clicar_dia(self, d): self.dia_selecionado = d; self.filtro_tipo_dash = None; self.atualizar_lista(); self.gerar_cal()
    def filtrar(self, e): self.termo_busca = self.ent_busca.get().lower(); self.atualizar_lista()
    def mes_ant(self): self.mes_atual -= 1; (self.mes_atual < 1 and self.set_dt(12, self.ano_atual-1)); self.gerar_cal()
    def mes_prox(self): self.mes_atual += 1; (self.mes_atual > 12 and self.set_dt(1, self.ano_atual+1)); self.gerar_cal()
    def set_dt(self, m, a): self.mes_atual, self.ano_atual = m, a
    def toggle_pend(self): self.mostrar_apenas_pendentes = self.sw_pend.get(); self.atualizar_lista()

if __name__ == "__main__":
    app = GestorTrabalhoRAM()
    app.attributes("-topmost", True); app.mainloop()