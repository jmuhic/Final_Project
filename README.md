# Final_Project
SI 507 Final Project

This program is intended as a way for a user to identify the most commonly reported reactions for a particular drug and, in reverse, to find the most commonly reported drug for a selected reaction.  The user will also have the ability to graphically view information based on age and gender.  Information has been taken from the FDA Adverse Event Reporting (FAERS) database, which is available to the public.  However, one must note that there are quality data issues within the database beyond the control of the FDA.  Therefore, there may be duplicate entries or bad data.   Due to the sheer volume of reports, the quantity of bad data is not likely to have much of an impact on the most commonly reported drugs or reactions.  Please do not infer causation based on the results displayed, as there may be other factors which may impact a patient’s reaction to a drug or combination of drugs.  Users will also have the option to display a sample list of reports.  For access to the complete reports, on must place a request to the FDA through the Freedom of Information Act (FOIA). 

For searches, please also keep in mind that spelling may impact your search.  The language in the FDA tends to use more medical terminology.  For example, one should use the term ‘diarrhoea’ as opposed to the more commonly used spelling in the U.S of ‘diarrhea’ for a search related to Reactions.

In addition to pulling information from FAERS, users who have a Reddit account will have the option to view comment threads from Reddit related to a search for a particular drug.  This is intended to allow the user to see what the overall community may be saying about a particular drug as opposed to what may only be reported by the medical community to the FDA.

API KEYS: <br/> API keys and passwords can be accessed through the secret_drugs.py file.  This file must be in the same directory as the program.  The program will import the required keys and passwords.


REQUIRED PACKAGES: <br/>
import requests <br/> 
import textwrap	<br/>
import urllib <br/> 
import json <br/> 
import plotly.express as px <br/>             	
import urllib.parse <br/> 
import os <br/> 
import numpy <br/>     	
import click <br/>
import webbrowser <br/>  	
from flask import Flask <br/> 	
from prettytable import PrettyTable <br/> 
import secret_drugs <br/> 	
from flask import request <br/> 	
from pandas import DataFrame <br/> 
import sqlite3 <br/> 	
import logging <br/> 	
plotly.graph_objects as go <br/> 
import plotly <br/> 	
import requests.auth <br/> 	
from textwrap import fill <br/> 
