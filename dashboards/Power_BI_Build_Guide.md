# Power BI Build Guide (Windows)

**Project:** UC15 - Enterprise Resource Planning Data Platform (ERPDP)  
**Use with:** `dashboards/Dashboard_Design.md` (what every page contains and the numbers to check)

---

This guide takes you from an empty Power BI file to the finished dashboard on a Windows laptop. Plan about **three hours** for all nine pages, or about **two hours** if you build pages 1 to 6 and page 9 only. These are estimates. The steps are written from how Power BI Desktop normally works. We could not test them inside Power BI, so menu names can differ slightly in your version.

## 1. Before you leave (on your Mac)

1. Check that everything is pushed: `git status --short` prints nothing, and the repository on GitHub shows the `dashboards/` folder with its `data/` subfolder.
2. Copy the `dashboards/` folder (about 8 MB) to a USB stick as a backup.
3. Ask your teammate to confirm that the laptop runs Windows 10 or 11 and has internet, to download Power BI Desktop.

## 2. On the Windows laptop

### Step 1. Install Power BI Desktop

Open the Microsoft Store, search for **Power BI Desktop** and install it. It is free, and you do not need to sign in to build a report. You would need a work or school account only to publish it online, which this project does not require.

### Step 2. Get the project files

If the project folder is already on the laptop, open a terminal in it and run `git pull origin main`. Otherwise, on GitHub choose *Code > Download ZIP* and unzip it. Check that the folder `dashboards\data` holds **12 CSV files** (the 11 views and `layer_reconciliation.csv`).

### Step 3. Start the report

Open Power BI Desktop, choose a blank report, and save it straight away as `UC15_ERP_Dashboard.pbix` inside the `dashboards` folder. Save again after each page.

### Step 4. Two settings to change before loading data

Open *File > Options and settings > Options*.

1. Under **Current File > Data Load**, untick **Autodetect new relationships after data is loaded**. Our tables are separate on purpose. If Power BI links them by matching column names (for example `item_id` or `category`), the numbers on the pages would be wrong.
2. Under **Current File > Regional Settings**, set the locale for import to **English (United States)**. This makes sure that decimal points are read correctly on a laptop set to another region.

### Step 5. Load the 12 files

Choose *Home > Get data > Text/CSV*, select a file, and click **Load**. Repeat for each file. The table in Power BI is named after the file (for example `vw_dash_sales`), and the measures in Step 8 rely on these exact names.

Check each table in the **Data view** (the table icon on the left). The bottom bar says *Table: name (N rows)*. The numbers must match:

| Table | Rows |
|---|---|
| `layer_reconciliation` | 10 |
| `vw_dash_assets` | 1,245 |
| `vw_dash_customers` | 1,500 |
| `vw_dash_data_checks` | 32 |
| `vw_dash_employees` | 35 |
| `vw_dash_finance` | 1,000 |
| `vw_dash_inventory_demand` | 12,000 |
| `vw_dash_manufacturing` | 1,000 |
| `vw_dash_procurement` | 1,300 |
| `vw_dash_receivables` | 45,839 |
| `vw_dash_sales` | 1,000 |
| `vw_dash_warehouse` | 3,204 |

Then open the **Model view** (the diagram icon). There must be **no lines** between the tables. If any appear, click a line and press Delete.

### Step 6. Set sort order and summaries

In the Data view, select a column and use the *Column tools* tab.

| Table and column | Setting |
|---|---|
| `vw_dash_sales[month_name]` | Sort by column: `month` |
| `vw_dash_inventory_demand[month_name]` | Sort by column: `month_number` |
| Dates (`sale_date`, `order_date`, `order_month`, `doc_date`, `doc_month`, `transaction_month` and the other date columns) | Data type: Date |
| ID-like numbers (`document_no`, `cust_num`, `employee_number`) and years (`year`, `doc_year`, `order_year`, `registration_year`, `install_year`) | Summarization: **Don't summarize**, so they are never added up by accident |

### Step 7. Apply the colour theme

*View > Themes > Browse for themes*, then choose `dashboards\UC15_theme.json`. The colours are the dark teal, green and gold used in the project documents.

### Step 8. Add the measures

There are 36 measures, listed in `Dashboard_Design.md`, Section 5.

**Option A, all at once (faster).** Open the **DAX query view** (the fourth icon on the left, or *View > DAX query view*). Open `dashboards\measures_dax_query.txt` in Notepad, copy everything and paste it into the query editor. Click **Update model with changes**. When it finishes, the 36 measures appear in the Data pane under their tables. If your version has no DAX query view, or the button does not appear, use Option B.

**Option B, one by one.** Select the table, click *Home > New measure*, paste one line from Section 5 of the design document, and press Enter. Repeat for each measure.

**Check:** put a Card on a page and drag `Total Revenue` into it. It must show **456,000**. Remove the test card afterwards.

Then format the percentage measures (*Measure tools > Format > Percentage*): `Cancelled Cost Share`, `Delay Rate`, `Consistent Dates Share`, `Failed Job Rate`, `Completed Job Rate`, `Low Efficiency Share`, `Obsolete Asset Share`, `Active Customer Share` and `Avg Fulfilment Rate`. Use zero decimals for the big amounts.

### Step 9. Build the pages

Build them in this order. Page 2 comes first because it is the simplest, and the others follow the same pattern.

| Order | Page | Time |
|---|---|---|
| 1 | Page 2. Sales | 20 min |
| 2 | Page 3. Procurement | 20 min |
| 3 | Page 4. Receivables | 20 min |
| 4 | Page 5. Inventory and warehouse | 25 min |
| 5 | Page 6. Manufacturing and assets | 25 min |
| 6 | Page 1. Executive overview | 15 min |
| 7 | Page 9. Data trust | 15 min |
| 8 | Page 7. Customers and employees (optional) | 15 min |
| 9 | Page 8. Finance (optional) | 10 min |

For every page:

1. Add a new page at the bottom and name it, for example `2 Sales`.
2. Add a **text box** at the top with the question the page answers (from `Dashboard_Design.md`).
3. Add each visual from the page table in `Dashboard_Design.md`: choose the visual type, then drag the listed fields into *Axis*, *Legend* or *Values*.
4. Add the **caveat text box** with the wording given for that page. Do not leave it out: it is what keeps the page honest.
5. Compare every card and chart with the **Check** table of that page. Fix any difference before moving on (see Section 3).
6. Keep a page to about eight visuals, use the same visual types in the same places on every page, and save.

Tip: a visual can be copied with Ctrl+C and pasted on another page. Change its fields afterwards.

### Step 10. Finish and bring it back

1. Save the file.
2. *File > Export > Export to PDF* (all pages), and save it as `UC15_ERP_Dashboard.pdf` in the `dashboards` folder.
3. Take a screenshot of each page (the Windows Snipping Tool is enough) and put them in `dashboards\screenshots\`.
4. Commit and push from the laptop (or copy the three items to your Mac and push from there):

```
git add dashboards/UC15_ERP_Dashboard.pbix dashboards/UC15_ERP_Dashboard.pdf dashboards/screenshots
git commit -m "Add Power BI dashboard"
git push origin main
```

Only one person should edit the `.pbix` file at a time, because Git cannot merge it.

## 3. If something looks wrong

| What you see | Likely cause and fix |
|---|---|
| A card shows blank | The measure is in a different table than the one you expected, or a slicer on the page is filtering everything out. Clear the slicers. |
| A number is double or much too large | A relationship was created between tables. Delete it in the Model view (Step 5). |
| Months appear as April, August, December | The month name is not sorted by the month number (Step 6). |
| A date shows as text, or you cannot make a monthly axis | Set the column's data type to Date (Step 6). |
| An ID or a year is summed up in a chart | Set Summarization to Don't summarize (Step 6). |
| Decimals are wrong, for example 0.657 shows as 657 | The locale is not English (United States). Set it in Step 4 and reload the file. |
| `Update model with changes` is missing | Your version has no DAX query view. Create the measures one by one (Option B). |
| A number differs from the Check table | Check that the measure uses the right column. In particular, procurement spend must use `Spend (excl. cancelled)`, not the total cost. |

## 4. After you have finished

Send me the PDF or the screenshots, and I will update the project report (Section 9.1 and the summary table) and the final presentation, so that they describe the finished dashboard.
