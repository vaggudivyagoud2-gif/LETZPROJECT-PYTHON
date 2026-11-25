"""Optional Tkinter desktop interface; uses the same application data layer."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from .models import RainfallRecord, validate_record, CATEGORIES
from .analytics import Analytics
from .reports import Reports
from .plotting import create_charts

class RainfallGUI:
    def __init__(self, app):
        self.app=app; self.root=tk.Tk(); self.root.title("Rainfall Data Explorer"); self.root.geometry("1120x720"); self.root.minsize(900,600)
        self.root.configure(bg="#f3f6fb")
        style=ttk.Style(); style.theme_use("clam"); style.configure("Treeview",rowheight=30,font=("Segoe UI",10),background="white",fieldbackground="white")
        style.configure("Treeview.Heading",font=("Segoe UI",10,"bold"),background="#e8eef8")
        self.build(); self.refresh()
    def build(self):
        top=tk.Frame(self.root,bg="#14213d",height=105); top.pack(fill="x"); top.pack_propagate(False)
        tk.Label(top,text="Rainfall Data Explorer",font=("Segoe UI",23,"bold"),fg="white",bg="#14213d").pack(anchor="w",padx=28,pady=(18,0))
        tk.Label(top,text="FUTUREREADY HACK  /  ENVIRONMENT & SUSTAINABILITY",font=("Segoe UI",9),fg="#a9c1e8",bg="#14213d").pack(anchor="w",padx=30)
        body=tk.Frame(self.root,bg="#f3f6fb"); body.pack(fill="both",expand=True,padx=24,pady=20)
        cards=tk.Frame(body,bg="#f3f6fb"); cards.pack(fill="x",pady=(0,15)); self.metrics=[]
        for title in ["Observations","Total rainfall","Average / record","Wettest reading"]:
            c=tk.Frame(cards,bg="white",highlightbackground="#e0e7f0",highlightthickness=1); c.pack(side="left",fill="x",expand=True,padx=(0,10))
            tk.Label(c,text=title.upper(),font=("Segoe UI",8,"bold"),fg="#6b7890",bg="white").pack(anchor="w",padx=15,pady=(12,2))
            v=tk.Label(c,text="—",font=("Segoe UI",17,"bold"),fg="#14213d",bg="white"); v.pack(anchor="w",padx=15,pady=(0,12)); self.metrics.append(v)
        toolbar=tk.Frame(body,bg="#f3f6fb"); toolbar.pack(fill="x",pady=(0,12))
        for label,cmd in [("＋ Add record",self.add),("Edit selected",self.edit),("Delete selected",self.delete),("Import CSV",self.import_csv),("Export reports",self.export),("Generate charts",self.charts)]:
            ttk.Button(toolbar,text=label,command=cmd).pack(side="left",padx=(0,7))
        searchrow=tk.Frame(body,bg="#f3f6fb"); searchrow.pack(fill="x",pady=(0,8))
        tk.Label(searchrow,text="Search",bg="#f3f6fb",fg="#43516a").pack(side="left")
        self.query=tk.StringVar(); ent=ttk.Entry(searchrow,textvariable=self.query,width=35); ent.pack(side="left",padx=8); ent.bind("<KeyRelease>",lambda e:self.refresh())
        self.category=tk.StringVar(value="All"); ttk.Combobox(searchrow,textvariable=self.category,values=["All",*CATEGORIES],state="readonly",width=14).pack(side="left"); self.category.trace_add("write",lambda *_:self.refresh())
        panel=tk.Frame(body,bg="white",highlightbackground="#e0e7f0",highlightthickness=1); panel.pack(fill="both",expand=True)
        cols=("id","date","location","rainfall_mm","category","notes"); self.tree=ttk.Treeview(panel,columns=cols,show="headings")
        for col,title,width in [("id","ID",105),("date","DATE",115),("location","LOCATION",180),("rainfall_mm","RAINFALL (MM)",130),("category","CATEGORY",115),("notes","NOTES",350)]: self.tree.heading(col,text=title); self.tree.column(col,width=width,anchor="w")
        y=ttk.Scrollbar(panel,orient="vertical",command=self.tree.yview); self.tree.configure(yscrollcommand=y.set); self.tree.pack(side="left",fill="both",expand=True,padx=8,pady=8); y.pack(side="right",fill="y")
        self.status=tk.Label(body,text="Ready · Changes are saved automatically",bg="#f3f6fb",fg="#77849a",font=("Segoe UI",9)); self.status.pack(anchor="w",pady=(8,0))
    def refresh(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        found=Analytics.search(self.app.records,self.query.get(),self.category.get())
        for r in found: self.tree.insert("","end",values=(r.record_id,r.date,r.location,f"{r.rainfall_mm:.2f}",r.category,r.notes))
        s=Analytics.summary(self.app.records); vals=[str(s['count']),f"{s['total']:.1f} mm",f"{s['average']:.1f} mm",f"{s['maximum']:.1f} mm"]
        for label,val in zip(self.metrics,vals): label.config(text=val)
        self.status.config(text=f"Showing {len(found)} of {len(self.app.records)} records · Auto-save enabled")
    def selected(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("Select a record","Choose a row first."); return None
        rid=self.tree.item(sel[0],"values")[0]; return next((r for r in self.app.records if r.record_id==rid),None)
    def form(self,title,r=None):
        win=tk.Toplevel(self.root); win.title(title); win.configure(bg="white"); win.resizable(False,False); win.transient(self.root); win.grab_set()
        fields={"Date (YYYY-MM-DD)":r.date if r else "","Location":r.location if r else "","Rainfall (mm)":str(r.rainfall_mm) if r else "","Category":r.category if r else "Normal","Notes":r.notes if r else ""}; widgets={}
        for i,(name,value) in enumerate(fields.items()):
            tk.Label(win,text=name,bg="white",fg="#263650",font=("Segoe UI",10)).grid(row=i,column=0,sticky="w",padx=18,pady=9)
            if name=="Category": w=ttk.Combobox(win,values=CATEGORIES,state="readonly",width=30); w.set(value)
            else: w=ttk.Entry(win,width=33); w.insert(0,value)
            w.grid(row=i,column=1,padx=18,pady=9); widgets[name]=w
        def save():
            d=widgets["Date (YYYY-MM-DD)"].get(); loc=widgets["Location"].get(); rain=widgets["Rainfall (mm)"].get(); cat=widgets["Category"].get(); notes=widgets["Notes"].get()
            ok,msg,val=validate_record(d,loc,rain,cat)
            if not ok: messagebox.showerror("Invalid input",msg,parent=win); return
            if r: r.date=d; r.location=loc; r.rainfall_mm=val; r.category=cat; r.notes=notes; action="Edited " + r.record_id
            else: new=RainfallRecord.create(d,loc,val,cat,notes); self.app.records.append(new); action="Added " + new.record_id
            self.app.persist(action); win.destroy(); self.refresh()
        ttk.Button(win,text="Save record",command=save).grid(row=6,column=1,sticky="e",padx=18,pady=16)
    def add(self): self.form("Add rainfall record")
    def edit(self):
        r=self.selected()
        if r: self.form("Edit rainfall record",r)
    def delete(self):
        r=self.selected()
        if r and messagebox.askyesno("Confirm deletion",f"Delete {r.record_id}?"):
            self.app.records.remove(r); self.app.persist("Deleted "+r.record_id); self.refresh()
    def import_csv(self):
        path=filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
        if not path:return
        try: records,errors=self.app.store.import_csv(path); self.app.records.extend(records); self.app.persist(f"Bulk imported {len(records)} rows"); self.refresh(); messagebox.showinfo("Import complete",f"Imported {len(records)} records. Rejected {len(errors)} rows.\n"+"\n".join(errors[:10]))
        except Exception as e: messagebox.showerror("Import failed",str(e))
    def export(self):
        paths=Reports.export(self.app.records,self.app.exports); messagebox.showinfo("Reports exported","\n".join(str(p) for p in paths if p.exists()))
    def charts(self):
        try: paths=create_charts(self.app.records,self.app.charts); messagebox.showinfo("Charts created","\n".join(str(p) for p in paths))
        except Exception as e: messagebox.showerror("Chart error",str(e))
    def run(self): self.root.mainloop()

def launch(app): RainfallGUI(app).run()
