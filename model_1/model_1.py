"""
Problem Statement: Extract values from Invoice documents

Solution Approach: Used pytesseratct, Regular Expressions and Case Statements
                   to extract data from image, search and filter out string
                   patterns with OOP concept.
"""

#importing libraries
import os
from tqdm import tqdm
import pandas as pd
import numpy as np
import re
import json
import warnings
import pytesseract
from pytesseract import Output 
from pdf2image import convert_from_path 
import cv2


warnings.filterwarnings("ignore")

#Creating class
class NLP():
    
    def __init__(self, pdf):
        """
        Input: pdf file
        """
        self.pdf = pdf
        self.extracted_data = {"invoice_number": None, "invoice_date": None, 
                          "total_amount": None, "tax_amount": None}
    
    
    def pdf_to_image(self):
        """
        Input : pdf file
        Output : image file in jpg format
        """
        
        pages = convert_from_path("Invoice_PDF\\"+self.pdf)
        
        dir_path = os.getcwd() + "\\invoice_image\\" + self.pdf.rstrip('.pdf')
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        for e,page in enumerate(pages):    
            img_file = dir_path + "\\" + self.pdf.rstrip(".pdf") +"_page" + str(e) + ".jpg"
            if not os.path.isfile(img_file):
                page.save(img_file, 'JPEG') 


    def __ocr(self, img):
        """
        getting data from image 
        
        Input : image file
        Output : data in dictionary format
        """
        data = pytesseract.image_to_data(img, output_type=Output.DICT, config=r'--oem 3 --psm 6')
        
        return data
    
    
    def __boundary_box(self, img, x, y, w, h):
        """
        creating box for the required data
        """
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        return img
    
    
    def __get_inv_date(self, rng, d, image, date_key_pattern, date_pattern):
        """
        Output : image file with boundary box on date
        """
        for i in range(rng):
            
            date_cnfrm = [True for j in d['text'][:i] if re.match(date_key_pattern, j)]
            condition_1 = int(d['conf'][i]) > 30 and re.fullmatch(date_pattern, d['text'][i]) and re.fullmatch(r'DUE|Order|P[/]O', d['text'][i-2]) == None and True in date_cnfrm and re.fullmatch(r'ORIGINAL', d['text'][i-4]) == None
            condition_2 = int(d['conf'][i]) > 30 and int(d['conf'][i]) > 30 and re.fullmatch(date_pattern, d['text'][i]) and re.fullmatch(r'DUE|Order|P[/]O', d['text'][i-2]) == None and re.fullmatch(r'Due', d['text'][i-5]) == None and re.fullmatch(r'ORIGINAL', d['text'][i-4]) == None
            
            if condition_1 == True or condition_2 == True:
                
                (l, t, d1, d2) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])

                if "DEG" in d['text'][i]:
                    
                    r = d['text'][i].rstrip(')').lstrip("Date|").replace('DEG','DEC')
                    r = r[:-2]+"-"+r[-2:]
                                    
                else:
                    
                    r = d['text'][i].rstrip(')').lstrip("Date|")
                    
                self.extracted_data["invoice_date"] = r
                image = self.__boundary_box(image, l, t, d1, d2)
                    
                break
            
            elif (True in date_cnfrm and re.match(r'\D+|\d["][.]', d['text'][i]) and rng - i >= 3 and re.match(r'\w+', d['text'][i+1]) and re.fullmatch(r'2\d{3}', d['text'][i+2])) or (re.match(r'\D+|\d["][.]', d['text'][i]) and rng - i >= 3 and re.match(r'\w+', d['text'][i+1]) and re.fullmatch(r'2\d{3}', d['text'][i+2])):
                
                (l, t, d1, d2) = (d['left'][i], d['top'][i], d['width'][i] + 32 + 92 + 45, d['height'][i])
                
                r = d['text'][i]+" "+d['text'][i+1]+" "+d['text'][i+2]
                
                self.extracted_data["invoice_date"] = r
                image = self.__boundary_box(image, l, t, d1, d2)
                
                break
            
        return image
    
    
    def __get_inv_no(self, rng, d, image, invoice_key_pattern, invoice_no_pattern,
                     date_key_pattern, date_pattern):
        """
        Output : image file with boundary box on invoice number
        """
        s = None
        
        for e,i in enumerate(d['text'][:]):
            
            condition_1 = re.match(invoice_key_pattern, i) and not re.match(date_key_pattern, d['text'][e+1]) and not re.fullmatch(r'E-mail:|BILL', d['text'][e+2])
            condition_2 = re.match(r'^Inv|^INV|^inv',i) and not re.match(r'^Net|if|Date|ENCLOSED|Issued|due', d['text'][e+1]) and not re.match(r'^ORIGI|the|Companies”|from', d['text'][e-1]) and not re.search(r'\d', i)
                
            if condition_1 == True:
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
                
                condition_3 = int(d['conf'][i]) > 30 and re.match(invoice_no_pattern, d['text'][i].lstrip('|No.')) and not re.search(r'[/%$.)(:|]|]|'+date_pattern, d['text'][i].lstrip('|No.')) and not re.match('Taxpayer', d['text'][i-2]) and not re.match('SSIC', d['text'][i+2]) 

                if condition_3 == True and not re.match('Taxpayer', d['text'][i-2]) and not re.match('SSIC', d['text'][i+2]) and not 'DUNS:' in d['text'][i-3:i+1]:
                    
                    if re.fullmatch(r'\d+', d['text'][i+1]):
                        
                        r = d['text'][i].lstrip("{") + " " + d['text'][i+1]
                        
                        (l, t, d1, d2) = (d['left'][i], d['top'][i], d['width'][i]+d['width'][i+1], d['height'][i])
                        
                    elif re.fullmatch(r'-', d['text'][i+1]) and re.fullmatch(r'[A-Z]{4}', d['text'][i+2]):
                        
                        r = d['text'][i].lstrip("{") + d['text'][i+1] + d['text'][i+2]
                        
                        (l, t, d1, d2) = (d['left'][i], d['top'][i], d['width'][i] + d['width'][i+1] + d['width'][i+2] + 30, d['height'][i])
                                   
                    elif re.fullmatch(r'[A-Z]{2}[/]', d['text'][i-1]):
                        
                        r = d['text'][i-1] + d['text'][i].lstrip("{")
                        
                        (l, t, d1, d2) = (d['left'][i-1], d['top'][i], d['width'][i] + d['width'][i-1] + 30, d['height'][i])
                                    
                    else:
                        
                        r = d['text'][i].lstrip("{|No.")
                        
                        (l, t, d1, d2) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                        
                    self.extracted_data["invoice_number"] = r
                    image = self.__boundary_box(image, l, t, d1, d2) 
                                    
                    break
                        
        elif s == None:
                    
            for i in range(rng):
                
                condition_4 = int(d['conf'][i]) > 20 and re.match(invoice_no_pattern, d['text'][i]) and not re.search(r'[/%$.)(:,]', d['text'][i]) and re.fullmatch(r'\d{1}|'+date_pattern, d['text'][i]) == None and re.search(r'[^Date]\D{2,}', d['text'][i+1]) == None
                condition_5 = int(d['conf'][i]) > 20 and re.match(invoice_no_pattern, d['text'][i]) and not re.search(r'[/%$.)(:,]', d['text'][i]) and re.fullmatch(r'\d{1}|'+date_pattern, d['text'][i]) == None and re.match(date_pattern, d['text'][i+1]) != None

                r = d['text'][i]
                
                (l, t, d1, d2) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                
                if condition_4 == True or condition_5 == True:
                    
                    self.extracted_data["invoice_number"] = r
                    image = self.__boundary_box(image, l, t, d1, d2)
                    
                    break
        
        return image
        
    
    def __get_tax_amnt(self, rng, d, image, n, cnt, tax_key_pattern, tax_pattern):
        """
        Output : image file with boundary box on tax amount if available
        """
        s = None
        
        if re.match(r'USD', d['text'][rng-2]):
            
            r = d['text'][rng-4].lstrip('[').rstrip(')')
            
            (l, t, d1, d2) = (d['left'][rng-4], d['top'][rng-4], d['width'][rng-4], d['height'][rng-4])
            
            self.extracted_data["tax_amount"] = r
            image = self.__boundary_box(image, l, t, d1, d2)
            
            return image
                
        for e,i in enumerate(d['text'][::-1][:]):
            
            condition_1 = re.match(tax_key_pattern, i.lstrip('\[')) and not re.match(r'[^(%)Exempt]\D{3,}', d['text'][::-1][e-1]) and "Edwards" not in d['text'][::-1]
            condition_2 = re.match(tax_key_pattern, i) and (re.match(tax_pattern, d['text'][::-1][e-2]) or re.match(r'^SHIPPING', d['text'][::-1][e-2])) and "Edwards" not in d['text'][::-1]
            condition_3 = not re.match(r'^VAT', i) and not re.match(r'^ID', d['text'][::-1][e-1]) and rng - e >= 3 and not re.match(r'work.', d['text'][::-1][e+1]) and not re.match(r'[[(]net]|US|EXTENDED', d['text'][::-1][e+2])
                      
            if condition_1 or condition_2:
                
                if re.match(r'^VAT', i) and len(i) == 3 and re.match(r'over', d['text'][::-1][e-1]):
                    s = rng-e-1+3
                    break
                
                elif re.fullmatch('Tax', i) and re.fullmatch("No\sTax", d['text'][::-1][e+1] + " " + d['text'][::-1][e+2]):
                    s = None
                    break
                    
                elif re.fullmatch(r'VAT', i) and not re.match(r'on', d['text'][::-1][e+1]) and not re.match(r'N°:', d['text'][::-1][e-1]):
                    s = rng-e-1
                    break
                
                elif not re.match(r'^VAT', i) and re.fullmatch(r'TOUR', d['text'][::-1][e+1]):
                    s = rng-e-1+3
                    break
                        
                elif not re.match(r'^VAT', i) and re.match(r'Use', d['text'][::-1][e+3]):
                    s = rng-e-3
                    break
                
                elif re.match(r'TAX', i) and re.match(r'^SHIPPING', d['text'][::-1][e-2]):
                    s = rng-e+5
                    break
                
                elif condition_3 == True:
                    s = rng-e-1
                    break
                
                else:
                    continue

        if s != None:  
                    
            for i in range(s, rng):
                        
                condition_4 = int(d['conf'][i]) > 20 and re.match(tax_pattern, d['text'][i].lstrip('-[)')) and not re.match(r'^%', d['text'][i+1]) and not re.search(r'[%-]', d['text'][i].lstrip('-'))
                        
                r = d['text'][i].lstrip('-[$').rstrip(')')
                        
                (l, t, d1, d2) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                        
                if condition_4 == True and not 'Ref:' in d['text'][i-4:i+1]:

                    self.extracted_data["tax_amount"] = r
                    image = self.__boundary_box(image, l, t, d1, d2)

                    break
    
        return image
    
    
    def __get_tot_amnt(self, rng, d, image, n, cnt, total_pattern):
        """
        Output : image file with boundary box on total amount 
        """
        s = None
        
        if re.match(r'USD', d['text'][rng-2]):
            
            r = d['text'][rng-1].rstrip(',)')
            
            (l, t, d1, d2) = (d['left'][rng-1], d['top'][rng-1], d['width'][rng-1], d['height'][rng-1])

            self.extracted_data["total_amount"] = r
            image = self.__boundary_box(image, l, t, d1, d2)
            
            return image
                
        for e,i in enumerate(d['text'][::-1][:]):
            
            condition_1 = (rng-e != rng-1 or re.match(total_pattern, d['text'][::-1][e-1])) and (re.match(r'^Tota|^TOTA|^tota|^tOTA|InvoiceTotal', i)) and (re.match(r'^Co|^Ca|^VI|^Em', d['text'][::-1][e-1]) == None) and (re.match(r'DOCKET', d['text'][::-1][e-2]) == None) and (re.match(r'^SUB|PriceTaxable|Sub|Prior|Line', d['text'][::-1][e+1]) == None)
            #condition_2 = re.match(r'^Co|^Ca|^VI|^Em', d['text'][::-1][e-1]) == None and re.match(r'DOCKET', d['text'][::-1][e-2]) == None and re.match(r'^SUB|PriceTaxable|Sub|Prior|Line', d['text'][::-1][e+1]) == None
            
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
                  
                if (re.match(r'^BAL|^Bal|^bal', i) and re.match(r'^DUE|^Due|^due', d['text'][::-1][e-1]) and i != 'BALANCES') or (re.match(r'^MONT|^Mont|^mont', i) and re.match(r'^PAY|^Pay|^pay', d['text'][::-1][e-1])) or (re.match(r'^AMO|^Amo|^amo', i) and re.match(r'^DUE|^Due|^due', d['text'][::-1][e-1])):
                    s = rng-e-1
                    break
        
        if s == None:
                    
            if cnt < n-1:
                for e,i in enumerate(d['text'][::-1][:]):
                    if re.search(r'Tota|TOTA|tota|tOTA', i) and (rng-e != rng-1) and not re.match('DISCOUNT', d['text'][::-1][e-1]) and not re.fullmatch(r'Line', d['text'][::-1][e+1]):
                        s = rng-e-1
                        break
                            
            elif s == None and cnt == n-1:
                for e,i in enumerate(d['text'][::-1][:]):
                    if re.match(total_pattern, i) and not re.search(r"[A-Z]|[-'/%]", i) and not re.search(r'["]', i) and not re.fullmatch(r'\d{1}', i) and not re.fullmatch(r'days', d['text'][::-1][e-1]):
                        s = rng-e-1
                        break
                       
        if s != None:

            for i in range(s, rng):
                
                condition_1 = int(d['conf'][i]) > 20 and re.match(total_pattern, d['text'][i]) and not re.search(r'[/%-]|\D{4,}', d['text'][i])  and not re.fullmatch(r'\d{1}', d['text'][i]) and not re.fullmatch(r'\d+/|Ref:', d['text'][i-1])
                
                r = d['text'][i].rstrip(',)]').lstrip('USD$')
                
                (l, t, d1, d2) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                
                if condition_1 == True and not 'Ref:' in d['text'][i-5:i+1]:

                    self.extracted_data["total_amount"] = r
                    image = self.__boundary_box(image, l, t, d1, d2)

                    break
        return image
    

    def extract(self):
        """               
        Output: extracted data in dictionary format
        """
        date_pattrn = r'\d{2}/\d{2}/\d{4}|\d{1}/\d{2}/\d{4}|\d{1}/\d{1}/\d{4}|\d{2}/\d{1}/\d{4}|\d{2}/\d{2}/\d{2}|\d{2}[-]\d{2}[-]\d{2}|\d{2}[.]\d{2}[.]\d{4}|\d{2}[-]\D{3}[-]\d{2}|\d{2}[-]\D{3}[-]\d{4}|\d{2}[-]\D{3}\d{2}|\d{2}[-]\d{2}[-]\d{4}|\d{2}\s\D{,7}\s\d{2}'
        date_key_pattrn = r'^Da|^DA|^da'
        inv_no_pattrn = r'\d+\D+|\D+\d+|\d+'
        inv_key_pattrn = r'Work|Order|STATEMENT|INV|^invoice|^INVOICE|^Invoice'
        tax_pattrn = r'^\d|^[$]\d|^[.]\d'
        tax_key_pattrn = r'^Tax|^TAX|^tax|^tAX|^VAT|Mwst'
        total_pattrn = r'^\d|^[$]\d|^US[$]\d'
        
        status = [0, 0, 0, 0]
        dir_path = os.getcwd() + "\\invoice_image\\" + self.pdf.rstrip('.pdf')
        img_files = os.listdir(dir_path)
        n_files = len(img_files)
        inv_img = None
        
        for c,file in enumerate(img_files):
            
            if status == [1, 1, 1, 1]:
                
                break
            
            else:
            
                inv_img = cv2.imread(dir_path + '\\' + file)
                
                dat = self.__ocr(inv_img)
                
                n_boxes = len(dat['text'])
             
                if status[0] == 0:
                    inv_img = self.__get_inv_date(n_boxes, dat, inv_img,
                                                  date_key_pattrn, date_pattrn)
                    status[0] = 1
                    
                if status[1] == 0:
                    inv_img = self.__get_inv_no(n_boxes, dat, inv_img,
                                                  inv_key_pattrn, inv_no_pattrn, 
                                                  date_key_pattrn, date_pattrn)
                    status[1] = 1
                
                if status[2] == 0:
                    inv_img = self.__get_tax_amnt(n_boxes, dat, inv_img, n_files,
                                                  c, tax_key_pattrn, tax_pattrn)
                    if self.extracted_data["tax_amount"] != None:
                        status[2] = 1
                        
                if status[3] == 0:
                    inv_img = self.__get_tot_amnt(n_boxes, dat, inv_img, n_files,
                                                  c, total_pattrn) 
                    if self.extracted_data["total_amount"] != None:
                        status[3] = 1
         

            img_path = os.getcwd() + "\\output_image\\" + self.pdf.rstrip('.pdf')
            if not os.path.exists(img_path):
                os.makedirs(img_path)
            cv2.imwrite(img_path + '\\' + file, inv_img)
            
        #print("\n",self.extracted_data)
        
        
         
def main():
    
    #creating directories to save output files
    folder_names = ["\\invoice_image", "\\output_image", "\\output_json"]
    for name in folder_names:
        if not os.path.exists(os.getcwd()+name):
            os.makedirs(os.getcwd()+name)
    json_path = os.getcwd() + "\\output_json\\"
    
    #getting list of input pdf file names 
    pdf_files = os.listdir(os.getcwd()+"\\Invoice_PDF")
    
    for file in tqdm(pdf_files):
        
        nlp = NLP(file)
        
        nlp.pdf_to_image()
        
        nlp.extract()
        
        #saving the dictionary output to local drive in json format
        js = json_path + file.rstrip('.txt') + ".json"
        
        with open(js, "w") as f:
            json.dump(nlp.extracted_data, f, indent = 6) 
            f.close()
            
if __name__ == "__main__":
    
    main()