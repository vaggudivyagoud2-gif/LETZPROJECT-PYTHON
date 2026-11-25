from pathlib import Path
from datetime import date
import os, sys, textwrap
from .models import RainfallRecord, validate_record, CATEGORIES
from .storage import Storage
from .analytics import Analytics
from .reports import Reports
from .plotting import create_charts

RESET="\033[0m"; CYAN="\033[96m"; BLUE="\033[94m"; GREEN="\033[92m"; YELLOW="\033[93m"; RED="\033[91m"; DIM="\033[2m"
def paint(s, c): return f"{c}{s}{RESET}" if sys.stdout.isatty() and os.getenv("NO_COLOR") is None else s

def ask(prompt, default=None):
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else (str(default) if default is not None else "")

def table(rows, headers):
    if not rows: print(paint("No records found.", DIM)); return
    widths=[max(len(str(h)), *(len(str(row.get(k,""))) for row in rows)) for k,h in headers]
    line="+-"+"-+-".join("-"*w for w in widths)+"-+"
    print(line); print("| "+" | ".join(str(h).ljust(w) for (_,h),w in zip(headers,widths))+" |\n"+line)
    for row in rows: print("| "+" | ".join(str(row.get(k,""))[:w].ljust(w) for (k,_),w in zip(headers,widths))+" |")
    print(line)

class App:
    def __init__(self, root=None):
        self.root=Path(root or Path(__file__).resolve().parents[1]); self.data=self.root/"data"; self.exports=self.root/"exports"; self.charts=self.root/"charts"
        self.store=Storage(self.data); self.records=self.store.load()
        if not self.records and (self.data/"sample_rainfall.csv").exists():
            imported, _ = self.store.import_csv(self.data/"sample_rainfall.csv"); self.records=imported; self.store.save(self.records)
    def persist(self, action): self.store.save(self.records); self.store.audit(f"{action}; records={len(self.records)}")
    def add(self):
        print(paint("\n  ADD RAINFALL OBSERVATION", CYAN))
        d=ask("Date YYYY-MM-DD", date.today().isoformat()); loc=ask("Location"); rain=ask("Rainfall (mm)"); cat=ask("Category (Normal/Heavy/Extreme/Light/Trace)","Normal"); notes=ask("Notes")
        ok,msg,val=validate_record(d,loc,rain,cat)
        if not ok: print(paint("✗ "+msg,RED)); return
        r=RainfallRecord.create(d,loc,val,cat,notes); self.records.append(r); self.persist("Added "+r.record_id); print(paint(f"✓ Saved record {r.record_id}",GREEN)); self.show_alerts()
    def show_records(self, records=None):
        records=self.records if records is None else records
        table([{"id":r.record_id,"date":r.date,"location":r.location,"mm":f"{r.rainfall_mm:.2f}","category":r.category,"notes":r.notes} for r in records],[("id","ID"),("date","DATE"),("location","LOCATION"),("mm","MM"),("category","CATEGORY"),("notes","NOTES")])
    def edit(self):
        rid=ask("Record ID to edit").upper(); r=next((x for x in self.records if x.record_id==rid),None)
        if not r: print(paint("Record not found.",RED)); return
        d=ask("Date",r.date); loc=ask("Location",r.location); rain=ask("Rainfall mm",r.rainfall_mm); cat=ask("Category",r.category); notes=ask("Notes",r.notes)
        ok,msg,val=validate_record(d,loc,rain,cat)
        if not ok: print(paint(msg,RED)); return
        r.date=d; r.location=loc; r.rainfall_mm=val; r.category=cat; r.notes=notes; self.persist("Edited "+rid); print(paint("Record updated.",GREEN))
    def delete(self):
        rid=ask("Record ID to delete").upper(); r=next((x for x in self.records if x.record_id==rid),None)
        if not r: print("Record not found."); return
        if ask(f"Delete {rid} ({r.date}, {r.location})? y/N","N").lower()=="y":
            self.records.remove(r); self.persist("Deleted "+rid); print(paint("Record deleted.",GREEN))
    def search(self):
        q=ask("Keyword (date/location/notes/ID)"); cats=["All",*CATEGORIES]; cat=ask("Category ("+"/".join(cats)+")","All"); loc=ask("Location (or All)","All")
        if cat not in cats: print("Unknown category; using All."); cat="All"
        self.show_records(Analytics.search(self.records,q,cat,loc))
    def summary(self):
        s=Analytics.summary(self.records); print(paint("\n  EXECUTIVE OVERVIEW",CYAN))
        cards=[("Records",s['count']), ("Total rainfall",f"{s['total']:.2f} mm"),("Average",f"{s['average']:.2f} mm"),("Median",f"{s['median']:.2f} mm"),("Maximum",f"{s['maximum']:.2f} mm"),("Minimum",f"{s['minimum']:.2f} mm"),("Dry records",s['dry_days']),("Wettest",s['wettest_day'])]
        for k,v in cards: print(f"  {paint(k.ljust(19),BLUE)} {v}")
        print("\n  MONTHLY BREAKDOWN"); table(Analytics.monthly(self.records),[("month","MONTH"),("total","TOTAL MM"),("average","AVG MM"),("records","COUNT")])
        print("  LOCATION BREAKDOWN"); table(Analytics.by_location(self.records),[("location","LOCATION"),("total","TOTAL MM"),("average","AVG MM"),("records","COUNT")]); self.show_alerts()
    def show_alerts(self):
        alerts=Analytics.alerts(self.records)
        if alerts:
            print(paint("\n  ⚠ DATA / THRESHOLD ALERTS",YELLOW))
            for a in alerts: print("  • "+a)
    def import_csv(self):
        path=ask("Path to CSV file")
        try: new,errors=self.store.import_csv(path)
        except (OSError,ValueError) as e: print(paint(f"Import failed: {e}",RED)); return
        self.records.extend(new); self.persist(f"Bulk imported {len(new)} rows")
        print(paint(f"Imported {len(new)} records; rejected {len(errors)} rows.",GREEN))
        for e in errors: print(paint("  "+e,YELLOW))
    def export(self):
        paths=Reports.export(self.records,self.exports); print(paint("Reports exported:",GREEN))
        for p in paths:
            if p.exists(): print("  "+str(p))
    def charts_action(self):
        try:
            for p in create_charts(self.records,self.charts): print(paint("Chart saved: ",GREEN)+str(p))
        except (RuntimeError,ValueError) as e: print(paint(str(e),YELLOW))
    def run(self):
        while True:
            print("\n"+paint("╭────────────────────────────────────────────────────────────╮",CYAN))
            print(paint("│                 RAINFALL DATA EXPLORER                      │",CYAN))
            print(paint("│              FUTUREREADY HACK · PROJECT #49                 │",CYAN))
            print(paint("╰────────────────────────────────────────────────────────────╯",CYAN))
            print(f"  {len(self.records)} records · Local JSON + CSV persistence\n")
            options=[("1","Add rainfall record"),("2","View all records"),("3","Edit a record"),("4","Delete a record"),("5","Search and filter"),("6","Analytics / executive summary"),("7","Import bulk CSV"),("8","Export reports (MD / TXT / CSV)"),("9","Generate trend charts"),("10","Launch graphical interface"),("0","Save and exit")]
            for n,label in options: print(f"  {paint(n,BLUE):<13} {label}")
            choice=ask("Select an option")
            actions={"1":self.add,"2":self.show_records,"3":self.edit,"4":self.delete,"5":self.search,"6":self.summary,"7":self.import_csv,"8":self.export,"9":self.charts_action}
            if choice in actions: actions[choice]()
            elif choice=="10":
                try:
                    from .gui import launch
                    launch(self)
                except Exception as e: print(paint(f"GUI unavailable: {e}",YELLOW))
            elif choice=="0": self.persist("Application closed"); print(paint("Data saved. Goodbye!",GREEN)); break
            else: print(paint("Please choose a listed option.",RED))
            input("\nPress Enter to continue...")

def main(): App().run()
