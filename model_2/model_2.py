"""
Problem Statement: Extract values from Invoice documents

Solution Approach: Used NLTK, Regular Expressions and Case Statements to tokenize, 
                   search and filter out string patterns with OOP concept.
"""

#importing libraries
import os
from tqdm import tqdm
import pandas as pd
import numpy as np
import re
import json
import warnings
from nltk.tokenize import WhitespaceTokenizer

warnings.filterwarnings("ignore")

#Creating class
class NLP():
    
    
    def __init__(self, text):
        """
        Input: pdf file
        """
        self.text = text
        self.extracted_data = {"invoice_number": None, "invoice_date": None, 
                          "total_amount": None, "tax_amount": None}
    

    def __tokenize(self):
        """
        Output : returns a dictionary having list of words
        """
        data = {'text':WhitespaceTokenizer().tokenize(self.text)}
        
        return data


    def __get_inv_date(self, rng, d, date_key_pattern, date_pattern):
        """
        Output : date
        """
        month_pattern = r'^JAN|^Jan|^jan|^FEB|^Feb|^feb|^MAR|^Mar|^mar|^APR|^Apr|^apr|^MAY|^May|^may|^JUN|^Jun|^jun|^JUL|^Jul|^jul|^AUG|^Aug|^aug|^SEP|^Sep|^sep|^OCT|^Oct|^oct|^NOV|^Nov|^nov|^DEC|^Dec|^dec'
        for i in range(rng):
            
            date_cnfrm = [True for j in d['text'][:i] if re.match(date_key_pattern, j)]
            condition_1 = re.fullmatch(date_pattern, d['text'][i]) and re.fullmatch(r'DUE|Order|P[/]O|Period', d['text'][i-2]) == None and re.fullmatch(r'Period', d['text'][i-1]) == None and True in date_cnfrm and re.fullmatch(r'ORIGINAL', d['text'][i-4]) == None and re.fullmatch(r'Letter', d['text'][i-3]) == None 
            condition_2 = re.fullmatch(date_pattern, d['text'][i]) and re.fullmatch(r'DUE|Order|P[/]O|Period', d['text'][i-2]) == None and re.fullmatch(r'Period', d['text'][i-1]) == None and re.fullmatch(r'Due', d['text'][i-5]) == None and re.fullmatch(r'ORIGINAL', d['text'][i-4]) == None and re.fullmatch(r'Letter', d['text'][i-3]) == None 
            condition_3 = True in date_cnfrm and re.fullmatch(r'DUE|Order|P[/]O|Period', d['text'][i-2]) == None and re.fullmatch(r'Period', d['text'][i-1]) == None and re.match(month_pattern+r'|\d["][.]|\d+', d['text'][i]) != None and rng - i >= 3 and re.match(r'\w+', d['text'][i+1]) != None and re.fullmatch(r'2\d{3}', d['text'][i+2]) != None and re.fullmatch(r'Delivery', d['text'][15]) == None
            
            if condition_1 == True or condition_2 == True:
                
                if 'FOLIO' == d['text'][4]:
                    break
                
                elif "DEG" in d['text'][i]:
                    
                    r = d['text'][i].rstrip(')').lstrip("Date|").replace('DEG','DEC')
                    r = r[:-2]+"-"+r[-2:]
                                        
                elif re.fullmatch(date_pattern, d['text'][i+3]) and 'US' == d['text'][i+4]:
                    
                    r = d['text'][i] + " , " + d['text'][i+3]
                                    
                else:
                    
                    r = d['text'][i].rstrip(')').lstrip("Date|")
                    
                self.extracted_data["invoice_date"] = r
                        
                break
            
            elif condition_3 == True or (re.match(month_pattern+r'|\d["][.]', d['text'][i]) and rng - i >= 3 and re.match(r'\w+', d['text'][i+1]) and re.fullmatch(r'2\d{3}', d['text'][i+2]) and not re.fullmatch(r'Date', d['text'][12]) and re.fullmatch(r'Delivery', d['text'][15]) == None):
                
                if d['text'][i+1] == "id":
                    r = d['text'][i]+" "+"1"+" "+d['text'][i+2]
                    
                else:
                    r = d['text'][i]+" "+d['text'][i+1]+" "+d['text'][i+2]
                
                self.extracted_data["invoice_date"] = r
                
                break
            
                
    def __get_inv_no(self, rng, d, invoice_key_pattern, invoice_no_pattern, 
                     date_key_pattern, date_pattern):
        """
        Output : invoice number
        """
        s = None
        
        for e,i in enumerate(d['text'][:]):
            
            no_cnfrm = [True for i in d['text'][e:e+6] if re.match(invoice_no_pattern, i.rstrip('.'))]
            condition_1 = re.match(invoice_key_pattern, i) and not re.fullmatch(date_key_pattern+'|Fed', d['text'][e+1]) and not re.fullmatch(r'E-mail:|BILL', d['text'][e+2]) and not re.fullmatch(r'E-mail:|BILL', d['text'][e+4]) and True in no_cnfrm and not re.fullmatch(r'ORIGINAL', d['text'][e-2])
            condition_2 = re.match(r'^Inv|^INV|^inv',i) and not re.match(r'^Net|if|Date|ENCLOSED|Issued|due', d['text'][e+1]) and not re.match(r'^ORIGI|the|Companies”|from', d['text'][e-1]) and not re.search(r'\d', i) 
            condition_3 = e != 0 and "INVOICE" not in d['text'][e+1:9] and "#" not in d['text'][e+1:9]

            if e == 0 and rng-e >= 14 and "Number"  == d['text'][e+13]:
                s = None
                break
            elif condition_1 == True:

                if i == 'STATEMENT' and re.match(r'^NO', d['text'][e+1]):
                    s = e
                    break
                elif (i == 'Work' and re.match(r'Order', d['text'][e+1])):
                    s = e
                    break
                elif condition_2 == True:
                    s = e
                    break
                else:
                    continue  

        if s != None:

            for i in range(s, rng):
                
                condition_3 = re.match(invoice_no_pattern, d['text'][i].lstrip('|No.').rstrip('.')) and not re.search(r'[%$.)(:|]|]|'+date_pattern, d['text'][i].lstrip('|No.').rstrip('.')) and not re.fullmatch('Taxpayer', d['text'][i-2]) and not re.fullmatch(r'SSIC', d['text'][i+2]) and not re.fullmatch(r'\d{1}', d['text'][i])

                if condition_3 == True and not 'DUNS:' in d['text'][i-3:i+1] and not re.match(r'^/', d['text'][i]):
                    
                    if re.fullmatch(r'\d+', d['text'][i+1]):
                        
                        r = d['text'][i].lstrip("{") + " " + d['text'][i+1]
                        
                    elif re.fullmatch(r'-', d['text'][i+1]) and re.fullmatch(r'[A-Z]{4}', d['text'][i+2]):
                        
                        r = d['text'][i].lstrip("{") + d['text'][i+1] + d['text'][i+2]
                                                
                    elif re.fullmatch(r'[A-Z]{4}', d['text'][i+1]) and re.fullmatch(r'DATE', d['text'][i+2]):
                        
                        r = d['text'][i].lstrip("{") + "-" + d['text'][i+1]
                        
                    elif re.fullmatch(r'[A-Z]{2}[/]', d['text'][i-1]):
                        
                        r = d['text'][i-1] + d['text'][i].lstrip("{")
                        
                    elif re.match(r'^1', d['text'][i]) and d['text'][i] == d['text'][i+2]:
                        
                        r = d['text'][i][1:]
                    
                    elif 'INV.' == d['text'][i-1]:
                        
                        r = ""

                        for j in range(i, rng):
                            if d['text'][j] == 'Î²' or d['text'][j] == 'β':
                                print(j)
                                for k in range(i, j+1, 2):
                                    r = r + "INV_" + d['text'][k] + " , " 
                                r = r.rstrip(" , ")
                                break
                        
                    elif re.fullmatch(r'Î²|β', d['text'][i+1]) and "INVOICE" == d['text'][i+2] and "#" == d['text'][i+3]:
                        
                         r = d['text'][i+5]
                                                  
                    else:
                        
                        r = d['text'][i].lstrip("{|No.").rstrip('.')
                        
                    self.extracted_data["invoice_number"] = r     
                                    
                    break
                        
        elif s == None:
                    
            for i in range(rng):
                
                condition_4 = re.match(invoice_no_pattern, d['text'][i]) and not re.search(r'[/%$.)(:,]|^Slip|Part', d['text'][i]) and re.fullmatch(r'\d{1}|'+date_pattern, d['text'][i]) == None and re.search(r'[^Date]\D{2,}', d['text'][i+1]) == None and re.fullmatch("Number|Net|Î²|β", d['text'][i-1]) == None and re.fullmatch(r'P[/]O|Vendor|Order', d['text'][i-2]) == None and re.fullmatch(r'Days', d['text'][i+1]) == None
                condition_5 = re.match(invoice_no_pattern, d['text'][i]) and not re.search(r'[/%$.)(:,]|^Slip|Part', d['text'][i]) and re.fullmatch(r'\d{1}|'+date_pattern, d['text'][i]) == None and re.match(date_pattern, d['text'][i+1]) != None and re.fullmatch("Number|Net|Î²|β", d['text'][i-1]) == None and re.fullmatch(r'P[/]O|Vendor|Order', d['text'][i-2]) == None and re.fullmatch(r'Days', d['text'][i+1]) == None

                r = d['text'][i]
                
                if condition_4 == True or condition_5 == True:
                    
                    if 'FOLIO' == d['text'][4]:
                        break
                    else:
                        self.extracted_data["invoice_number"] = r
                    
                    break
        
        
    def __get_tax_amnt(self, rng, d, tax_key_pattern, tax_pattern):
        """
        Output : tax amount
        """
        s = None
        
        if re.match(r'USD', d['text'][rng-2]):
            
            r = d['text'][rng-4].lstrip('[').rstrip(')')
            
            self.extracted_data["tax_amount"] = r
            
            return
                
        for e,i in enumerate(d['text'][::-1][:]):
            
            condition_1 = re.match(tax_key_pattern, i.lstrip('\[')) and not re.match(r'[^(%)ExemptTOTAL]\D{3,}', d['text'][::-1][e-1]) and not "Exempt" in d['text'][::-1][e:] and not re.fullmatch(r'description', d['text'][::-1][e+1]) and "Remarks" != d['text'][::-1][e-5] and "Remarks" != d['text'][::-1][e-8]
            condition_2 = re.match(tax_key_pattern, i) and (re.match(tax_pattern, d['text'][::-1][e-2]) != None or re.match(r'^SHIPPING', d['text'][::-1][e-2]) != None) and not "Exempt" in d['text'][::-1][e:] and "Remarks" != d['text'][::-1][e-5] and "Remarks" != d['text'][::-1][e-8]
            condition_3 = not re.match(r'^VAT', i) and not re.match(r'^ID', d['text'][::-1][e-1]) and rng - e >= 3 and not re.match(r'work.', d['text'][::-1][e+1]) and not re.fullmatch(r'[[(]net]|US|EXTENDED', d['text'][::-1][e+2]) 

            if condition_1 or condition_2:
                
                if re.fullmatch(r'VAT', i) and re.match(r'over', d['text'][::-1][e-1]):
                    s = rng-e-1+3
                    break
                
                elif re.fullmatch('Tax', i) and re.fullmatch(r"No\sTax", d['text'][::-1][e+1] + " " + d['text'][::-1][e+2]):
                    s = None
                    break
                
                elif re.fullmatch('Tax|MwSt', i) and re.fullmatch(r"Sales|Betrag", d['text'][::-1][e+4]):
                    s = rng-e-1-1
                    break
                
                elif re.fullmatch(r'VAT', i) and not re.match(r'on', d['text'][::-1][e+1]) and not re.match(r'N°:', d['text'][::-1][e-1]):
                    s = rng-e-1
                    break
                
                elif not re.match(r'^VAT', i) and re.fullmatch(r'TOUR', d['text'][::-1][e+1]):
                    s = rng-e-1+37
                    break
                        
                elif not re.match(r'^VAT', i) and re.match(r'Use', d['text'][::-1][e+3]):
                    s = rng-e-3
                    break
                
                elif re.match(r'TAX', i) and re.match(r'^SHIPPING', d['text'][::-1][e-2]):
                    s = rng-e+5
                    break
                
                elif re.fullmatch(r'Tax', i) and re.fullmatch(r'PAYMENT', d['text'][::-1][e-2]):
                    s = rng-e+7
                    break  
                
                elif re.fullmatch(r'Tax', i) and re.fullmatch(r'Amount|Extended', d['text'][::-1][e-2]):
                    for j in range(0, e):
                        if d['text'][::-1][j] == "Total":
                            s = rng-j-1-2
                            break
                    break
                
                elif condition_3 == True:
                    s = rng-e-1
                    break
                
                else:
                    continue

        if s != None:  
                    
            for i in range(s, rng):
                        
                condition_4 = re.match(tax_pattern, d['text'][i].lstrip('-[)')) and not re.match(r'^%', d['text'][i+1]) and not re.search(r'[%/-]', d['text'][i].lstrip('-'))
    
                r = d['text'][i].lstrip('-[$').rstrip(')')
                        
                if condition_4 == True and not 'Ref:' in d['text'][i-4:i+1]:

                    if re.fullmatch(r'CHARGES', d['text'][i-2]):
                        r = d['text'][i] + " , " + d['text'][i+2] 
                        
                    self.extracted_data["tax_amount"] = r

                    break
                
    
    def __get_tot_amnt(self, rng, d, total_pattern):
        """
        Output : total amount 
        """
        s = None
        
        if re.match(r'USD', d['text'][rng-2]):
            
            r = d['text'][rng-1].rstrip(',)')
            
            self.extracted_data["total_amount"] = r
            
            return
                
        for e,i in enumerate(d['text'][::-1][:]):
            
            condition_1 = (rng-e != rng-1 or re.match(total_pattern, d['text'][::-1][e-1])) and (re.match(r'^Tota|^TOTA|^tota|^tOTA|InvoiceTotal', i)) and (re.match(r'^Co|^Ca|^VI|^Em|demand|Long|Outbound', d['text'][::-1][e-1]) == None) and (re.match(r'DOCKET|Incoterms|Outbound', d['text'][::-1][e-2]) == None) and (re.match(r'^SUB|PriceTaxable|Sub|Prior|Line', d['text'][::-1][e+1]) == None) and (re.fullmatch(r'DESCRIPTION|PriceTaxable|please', d['text'][::-1][e+2]) == None) and ("Calls" != d['text'][::-1][e+7])
             
            if condition_1 == True:
                s = rng-e-1
                if True in [True for j in d['text'][s:] if re.match(r'[\d,.]{3,}|[$\d,.]{3,}', j) and not "$0.00" == j]:
                    break
                else:
                    continue
                       
        if s == None:
            
            for e,i in enumerate(d['text'][::-1][:]):
                
                if (re.match("^Invoi|^INVOI|^invoi'", i) and re.match(r'^AMO|^Amo|amo', d['text'][::-1][e-1])) or (re.match("Invoice.Amount", i)):
                    s = rng-e-1
                    break
                       
        if s == None:
            
            for e,i in enumerate(d['text'][::-1][:]):
                  
                if ((re.match(r'^BAL|^Bal|^bal', i) and re.match(r'^DUE|^Due|^due', d['text'][::-1][e-1]) and i != 'BALANCES') or (re.match(r'^MONT|^Mont|^mont', i) and re.match(r'^PAY|^Pay|^pay', d['text'][::-1][e-1])  and not re.fullmatch(r'After', d['text'][::-1][e-4])) or (re.match(r'^AMO|^Amo|^amo', i) and re.match(r'^DUE|^Due|^due', d['text'][::-1][e-1]))) or (re.match(r'CREDITS', i)):
                    s = rng-e-1
                    break
        
        if s == None:
                    
            for e,i in enumerate(d['text'][::-1][:]):
                if re.search(r'Tota|TOTA|tota|tOTA', i) and (rng-e != rng-1) and not re.match('DISCOUNT', d['text'][::-1][e-1]) and not re.fullmatch(r'Line', d['text'][::-1][e+1]):
                    s = rng-e-1
                    break
                  
        if s == None :
            
            for e,i in enumerate(d['text'][::-1][:]):
                if re.match(total_pattern, i) and not re.search(r"[A-Z]|[-'/%]", i) and not re.search(r'["]', i) and not re.fullmatch(r'\d{1}', i) and not re.fullmatch(r'days', d['text'][::-1][e-1]) and not re.fullmatch(r'After', d['text'][::-1][e+3]):
                    s = rng-e-1
                    break

        if s != None:

            for i in range(s, rng):
                
                condition_1 = re.match(total_pattern, d['text'][i]) and not re.search(r'[/%-]|\D{4,}', d['text'][i])  and not re.fullmatch(r'\d{1}', d['text'][i]) and not re.fullmatch(r'\d+/|Ref:', d['text'][i-1])
                
                r = d['text'][i].rstrip(',)]C').lstrip('USD$')
                              
                if condition_1 == True and not 'Ref:' in d['text'][i-5:i+1]:
                    
                    if "SL7" == d['text'][i-1]:
                        r = "17," + d['text'][i].lstrip('1USD$')

                        
                    elif "Cur" == d['text'][i-6]:
                        r = d['text'][i-3].lstrip('USD$') + " , " + d['text'][i].lstrip('USD$')

                    
                    elif "BALANCE" == d['text'][s] and "PAYMENT" == d['text'][s-1]:
                        r = d['text'][i+1].lstrip('USD$') + "." + d['text'][i+2]
                        
                    else:
                        pass
                    
                    self.extracted_data["total_amount"] = r
                    
                    break
    
    
    def extract(self):
        """               
        Output: extracted data in dictionary format
        """        
        date_pattrn = r'\d{2}/\d{2}/\d{4}|\d{1}/\d{2}/\d{4}|\d{1}/\d{1}/\d{4}|\d{2}/\d{1}/\d{4}|\d{2}/\d{2}/\d{2}|\d{2}[-]\d{2}[-]\d{2}|\d{2}[.]\d{2}[.]\d{4}|\d{2}[-]\D{3}[-]\d{2}|\d{2}[-]\D{3}[-]\d{4}|\d{2}[-]\D{3}\d{2}|\d{2}[-]\d{2}[-]\d{4}|\d{2}\s\D{,7}\s\d{2}'
        date_key_pattrn = r'^Da|^DA|^da'
        inv_no_pattrn = r'\d+\D+|\D+\d+|\d+'
        inv_key_pattrn = r'Work|Order|STATEMENT|INV|^invoice|^INVOICE|^Invoice'
        tax_pattrn = r'^\d|^[$]\d|^[.]\d'
        tax_key_pattrn = r'MwSt|^Tax|^TAX|^tax|^tAX|^VAT'
        total_pattrn = r'^\d|^[$]\d|^US[$]\d'

        dat = self.__tokenize()
                
        n_words = len(dat['text'])

        self.__get_inv_date(n_words, dat, date_key_pattrn, date_pattrn)
        
                    
        self.__get_inv_no(n_words, dat, inv_key_pattrn, inv_no_pattrn, 
                          date_key_pattrn, date_pattrn)

        self.__get_tax_amnt(n_words, dat, tax_key_pattrn, tax_pattrn)
                    
        
        self.__get_tot_amnt(n_words, dat, total_pattrn) 


        #print("\n",self.extracted_data)
            
         
def main():
    
    #creating directory to save output files
    if not os.path.exists(os.getcwd()+"\\output_json"):
        os.makedirs(os.getcwd()+"\\output_json")
    json_path = os.getcwd() + "\\output_json\\"
        
    #getting list of input text file names 
    text_files = os.listdir(os.getcwd()+"\\invoice_TXT")
                
    #Iterating the filenames in a for loop
    for file in tqdm(text_files):
        
        with open(os.getcwd()+"\\invoice_TXT"+"\\{}".format(file), 'r') as f:
            file_content = f.read()
            f.close()
            
        nlp = NLP(file_content)
        
        nlp.extract()
        
        #saving the dictionary output to output directory in json format
        js = json_path + file.rstrip('.txt') + ".json"
        
        with open(js, "w") as f:
            json.dump(nlp.extracted_data, f, indent = 6) 
            f.close()
        

if __name__ == "__main__":
    
    main()