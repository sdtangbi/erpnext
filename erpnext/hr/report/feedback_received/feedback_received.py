# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

#############Created by Cheten Tshering on 26/11/2020##########################
from __future__ import unicode_literals
import frappe

def execute(filters):
	if filters.get("corporate_ds") == "Feedback_Received":
		columns, data = get_individual_rating_columns(filters), get_individual_rating_data(filters)
	elif filters.get("corporate_ds") == "3Ds":
		columns, data = get_3ds_columns(filters), get_3ds_data(filters)
	elif filters.get("corporate_ds") == "Competency":
		columns, data = get_competency_columns(filters), get_competency_data(filters)
	elif filters.get("corporate_ds") == "Indicators":
		columns, data = get_detail_columns(filters), get_detail_data(filters)
	return columns, data


def get_individual_rating_columns(filters):
	columns = [
		("Employee Name") + ":Link/Employee:150",
		("recipient no") + "::150",
		("Designation") + "::220",
		("Feedback Received") + "::150",
		("Overall Rating ") + ":Int:150"

	]
	return columns

def get_individual_rating_data(filters):
	cond = get_conditions(filters)
	data = frappe.db.sql(
		"""
			select 
				fb.recipient_name, 
				fb.recipient,
				fb.designation,
				count(fb.recipient)/30,
				avg(fbi.rating)/5*100
			from 
				`tabFeedback` fb, `tabFeedback Item` fbi
			WHERE 
				fbi.parent=fb.name and fb.docstatus=1 {condition}	
			GROUP BY 
				fb.recipient
			HAVING count(fb.recipient)/30 > 1
		""".format(condition=cond)
	)	
	return data

def get_3ds_columns(filters):
	columns =[
		("3Ds") + "::150",
		("Employee name") + "::150",
		("Overall Rating(%)") + "::150"
	]
	return columns

def get_3ds_data(filters):
	cond = get_conditions(filters)
	data = frappe.db.sql(
		"""
			 select 
			 	c.corporate_ds, fb.recipient_name, round(avg(fbi.rating),1)/5*100
			 from 
			 	`tabFeedback` fb 
			inner join 
				`tabFeedback Item` fbi on fb.name = fbi.parent
			 inner join 
			 	`tabCompetency` c on fbi.competency_code=c.name 
			 where fb.docstatus=1 {condition}
			 group by c.corporate_ds;
		""".format(condition=cond)
	)
	return data

def get_competency_columns(filters):
	columns = [
		("Competency") + "::370",
		("Employee name") + "::150",
		("Overall Rating(%)") + "::150"
	]
	return columns

def get_competency_data(filters):
	cond = get_conditions(filters)
	data=frappe.db.sql(
		"""
		select fbi.competency, fb.recipient_name, round(avg(fbi.rating),1)/5*100
		from `tabFeedback` fb, `tabFeedback Item` fbi 
		where fb.name=fbi.parent and fb.docstatus=1 {condition}
		group by fbi.competency_code;
		""".format(condition=cond)
	)
	return data

def get_detail_columns(filters):
	columns=[
		("Indicators") + "::400",
		("Employee Name") + "::150",
		("Rating(%)") + "::100"
	]
	return columns

def get_detail_data(filters):
	cond = get_conditions(filters)
	data=frappe.db.sql(
		"""
		select fbi.detail, fb.recipient_name, round(fbi.rating,1)/5*100
		from `tabFeedback` fb, `tabFeedback Item` fbi 
		where fb.name=fbi.parent and fb.docstatus=1 {condition}
		group by fbi.detail;
		
		""".format(condition=cond)
	)
	return data
	
def get_conditions(filters):
	cond = ""
	if filters.fiscal_year:
		cond += "and fb.fiscal_year='{}'".format(filters.fiscal_year)
	if filters.recipient:
		cond += "and fb.recipient='{}'".format(filters.recipient)
	return cond


#select count(*) from `tabFeedback Recipient Item` fri, `tabEmployee` e where fri.employee= e.employee and fri.employee='1617' and e.status ="Active";
#select count(*) from `tabEmployee` where reports_to="1617";



