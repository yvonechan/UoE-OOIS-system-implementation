from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from datetime import datetime, timedelta, time

# Configuring flask app
app = Flask(__name__)

# Configuring mysql database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'codio'
app.config['MYSQL_DB'] = 'assignment'
mysql = MySQL(app)

class HealthcareProfessional:
  def __init__(self,name,employeeNumber):
    self._name=name
    self._employeeNumber=employeeNumber
  @property
  def name(self):
    return self._name
  @name.setter
  def name(self,new_name):
    self._name=new_name
  @property
  def employeeNumber(self):
    return self._employeeNumber
  @employeeNumber.setter
  def employeeNumber(self,new_employeeNumber):
    self._employeeNumber=new_employeeNumber
  #Add record to Consultations table
  def consultation(self,appointment_id,staff_id,consultation_notes):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(f'SELECT type FROM Appointments WHERE appointment_id={appointment_id}')
    rows=cursor.fetchall()
    if len(rows)>0 and rows[0][0]=="confirmed":
      cursor.execute(f'INSERT INTO Consultations (appointment_id,staff_id,consultation_notes) VALUES ({appointment_id},{staff_id},"{consultation_notes}")')
      conn.commit()
      return (f'Consultation of appointment id {appointment_id} is saved')
    else:
      return ("Invalid appointment ID")
    cursor.close()
    conn.close()

class Doctor(HealthcareProfessional):
  #Add record to Prescriptions table with default repeat_request = false
  def issuePrescription(self,patient_id,employeeNumber,drug,quantity,dosage):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO Prescriptions (patient_id,staff_id,drug,quantity,dosage,repeat_request) VALUES ({patient_id},{employeeNumber},"{drug}",{quantity},{dosage},0)')
    conn.commit()
    return ("Prescription issued")
    cursor.close()
    conn.close()
    

class Nurse(HealthcareProfessional):
  pass

class Patient:
  def __init__(self,name,address,phone):
    self._name=name
    self._address=address
    self._phone=phone
  @property
  def name(self):
    return self._name
  @name.setter
  def name(self,new_name):
    self._name=new_name
  @property
  def address(self):
    return self._address
  @address.setter
  def address(self,new_address):
    self._address=new_address
  @property
  def phone(self):
    return self._phone
  @phone.setter
  def name(self,new_phone):
    self._phone=new_phone
  #Mark true for the requestRepeat field in Prescriptions table
  def requestRepeat(self,prescription_id,patient_id):
    cursor = mysql.connection.cursor()
    #Check if the prescription exists
    cursor.execute(f'SELECT * FROM Prescriptions WHERE prescription_id ={prescription_id} AND patient_id={patient_id}')
    rows=cursor.fetchall()
    cursor.close()
    if len(rows)>0:
      conn = mysql.connection
      cursor = conn.cursor()
      cursor.execute(f'UPDATE Prescriptions SET repeat_request=1 WHERE prescription_id ={prescription_id}')
      conn.commit()
      return ("Prescription repeat request successful")
      cursor.close()
      conn.close()
    #No record match if input prescription id
    else:
      return ("No valid prescription was found")
  #Add record in Appointments table with type "requested"
  def requestAppointment(self,patient_id,appointment_time):
    #Suppose each timeslot can maximum cater 3 patients
    #Check if the timeslot already has 3 confirmed appointments
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM Appointments WHERE appointment_time="{appointment_time}" AND type="confirmed"')
    count=cursor.rowcount
    if count>=3:
      return ("Sorry, the selected slot has already been fully booked.")
    else:
      cursor.execute(f'INSERT INTO Appointments (patient_id,type,appointment_time) VALUES ({patient_id},"requested","{appointment_time}")')
      conn.commit()
      return ("Appointment request successful")
      cursor.close()
    
class Receptionist:
  def __init__(self,name,employeeNumber):
    self._name=name
    self._employeeNumber=employeeNumber
  @property
  def name(self):
    return self._name
  @name.setter
  def name(self,new_name):
    self._name=new_name
  @property
  def employeeNumber(self):
    return self._employeeNumber
  @employeeNumber.setter
  def employeeNumber(self,new_employeeNumber):
    self._employeeNumber=new_employeeNumber
  #Change the type of appointment from "requested" to "confirmed"
  def makeAppointment(self,appointment_id):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(f'UPDATE Appointments SET type="confirmed" WHERE appointment_id={appointment_id}')
    conn.commit()
    return (f'Appointment of ID {appointment_id} has been confirmed.')
    cursor.close()
  #Change the type of appointment to "cancelled"
  def cancelAppointment(self,appointment_id):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(f'UPDATE Appointments SET type="cancelled" WHERE appointment_id={appointment_id}')
    conn.commit()
    return (f'Appointment of ID {appointment_id} has been cancelled.')
    cursor.close()

class AppointmentSchedule:
  def __init__(self,appointments):
    self.appointments=appointments
  def addAppointment(self,patient_id,appointment_time):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO Appointments (patient_id,type,appointment_time) VALUES ({patient_id},"confirmed","{appointment_time}")')
    conn.commit()
    return ("Appointment Added.")
    cursor.close()
  def cancelAppointment(self,appointment_id):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(f'UPDATE Appointments SET type="cancelled" WHERE appointment_id={appointment_id}')
    conn.commit()
    return (f'Appointment of ID {appointment_id} Cancelled.')
    cursor.close()
  def determineStartTime(self,inputTime=datetime.now()):
    #Find the appropriate datetime to start searching
    now=inputTime
    start=datetime.now()
    nowTime=now.time()
    nowDate=now.date()
    closeTime=time(hour=18,minute=0,second=0,microsecond=0)
    #Logic determing the next available time slot
    if nowTime>closeTime:
        startDate=nowDate+timedelta(days=1)
        startTime=time(hour=9,minute=0,second=0,microsecond=0)
        start=datetime.combine(startDate,startTime)
    else:
        startDate=nowDate
        nowHour=now.hour
        nowMinute=now.minute
        if nowMinute==0:
          startHour=int(nowHour)
          startMinute=0
        elif nowMinute>30:
            startHour=int(nowHour)+1
            startMinute=0
        else:
            startHour=int(nowHour)
            startMinute=30
        start=datetime.combine(startDate,time(startHour,startMinute))
    return start
  def findNextAvailable(self):
    start=self.determineStartTime() 
    while(True):
      appointment_time=start.strftime("%Y-%m-%d %H:%M:%S")
      cursor = mysql.connection.cursor()
      #Assume every timeslot can take 3 consultations at maximum
      #Check if the timeslot already has 3 appointments
      cursor.execute(f'SELECT * FROM Appointments WHERE appointment_time="{appointment_time}"')
      count=cursor.rowcount
      cursor.close()
      if count<3:
        return (f'The next available appointment time slot for booking: {appointment_time}')
        break
      else:
        #Add 30 minutes to the time and search again
        newTime=start+timedelta(minutes=30)
        start=self.determineStartTime(newTime)

# Routes
# Login page and redirect according to identity
@app.route("/", methods =["GET", "POST"])
def index():
  if request.method == "POST":
    loginId=request.form.get('loginId')
    rank=request.form.get('rank')
    #For Staff, save the inputs as global variables for later use
    if rank=='staff':
      cursor = mysql.connection.cursor()
      cursor.execute(f'SELECT * FROM Staff WHERE staff_id ={loginId}')
      rows=cursor.fetchall()
      cursor.close()
      if len(rows)>0:
        global employeeNumber
        global staffName
        employeeNumber=rows[0][0]
        staffName=rows[0][2]
        staffRank=rows[0][1]
        if staffRank==1:
          return redirect(url_for('doctor_menu'))
        elif staffRank==2:
          return redirect(url_for('nurse_menu'))
        elif staffRank==3:
          return redirect(url_for('receptionist'))
        else:
          return render_template('response.html',message=f'Hello {staffName}')
      else:
        return render_template('response.html',message='Not valid Staff ID')
    #For Patient, save the inputs as global variables for later use
    elif rank=='patient':
      cursor = mysql.connection.cursor()
      cursor.execute(f'SELECT * FROM Patients WHERE patient_id ={loginId}')
      rows=cursor.fetchall()
      cursor.close()
      if len(rows)>0:
        global patientId
        global patientName
        global patientAddress
        global patientPhone
        patientId=rows[0][0]
        patientName=rows[0][4]
        patientAddress=rows[0][2]
        patientPhone=rows[0][3]
        return redirect(url_for('patient'))
      else:
        return render_template('response.html',message='Not valid Patient ID')
  return render_template('index.html',title='System Implementation Assignment - Landing Page')

#Patient Page
@app.route("/patient", methods =["GET", "POST"])
def patient():
  patient=Patient(patientName,patientAddress,patientPhone)
  if request.method == "POST":
    buttonAction=request.form.get('btn')
    #Request repeat
    if buttonAction=='Request Repeat':
      prescriptionId=request.form.get('prescriptionId')
      if prescriptionId!='':
        message=patient.requestRepeat(prescriptionId,patientId)
      else:
        message="Invalid input."
      return render_template('response.html',message=message)
    #Request appointment
    elif buttonAction=='Request Appointment':
      appointmentDate=request.form.get('appointmentDate')
      appointmentHour=request.form.get('appointmentHour')
      appointmentMinute=request.form.get('appointmentMinute')
      appointmentDatetime=appointmentDate+' '+appointmentHour+':'+appointmentMinute+':00'
      if appointmentDate!='' and appointmentHour!='' and appointmentMinute!='':
        message=patient.requestAppointment(patientId,appointmentDatetime)
      else:
        message="Invalid input."
      return render_template('response.html',message=message)
  return render_template('patient.html',title='System Implementation Assignment - Patient Portal')

#Doctor Page
@app.route("/doctor_menu", methods =["GET"])
def doctor_menu():
  return render_template('doctor_menu.html',title='System Implementation Assignment - Doctor Portal')

#Nurse Page
@app.route("/nurse_menu", methods =["GET"])
def nurse_menu():
  return render_template('nurse_menu.html',title='System Implementation Assignment - Nurse Portal')

#Issue Prescription Page
@app.route("/issue_prescription", methods =["GET","POST"])
def issue_prescription():
  doctor=Doctor(staffName,employeeNumber)
  if request.method == "POST":
    inputPatientId=request.form.get('patientId')
    drug=request.form.get('drug')
    quantity=request.form.get('quantity')
    dosage=request.form.get('dosage')
    message=doctor.issuePrescription(inputPatientId,employeeNumber,drug,quantity,dosage)
    return render_template('response.html',message=message)
  return render_template('issue_prescription.html',title='System Implementation Assignment - Issue Prescription')

#Consultation Page
@app.route("/consultation", methods =["GET","POST"])
def consultation():
  hcp=HealthcareProfessional(staffName,employeeNumber)
  if request.method == "POST":
    appointment_id=request.form.get('appointmentId')
    consultation_notes=request.form.get('notes')
    message=hcp.consultation(appointment_id,employeeNumber,consultation_notes)
    return render_template('response.html',message=message)
  return render_template('consultation.html',title='System Implementation Assignment - Consultation')

#Receptionist Page
@app.route("/receptionist",methods=["GET","POST"])
def receptionist():
  receptionist=Receptionist(staffName,employeeNumber)
  if request.method == "POST":
    buttonAction=request.form.get('btn')
    #Confirm Appointment
    if buttonAction=='Confirm Appointment':
      confirmId=request.form.get('confirmId')
      if confirmId!='':
        message=receptionist.makeAppointment(confirmId)
      else:
        message="Invalid input."
      return render_template('response.html',message=message)
    #Cancel Appointment
    elif buttonAction=='Cancel Appointment':
      cancelId=request.form.get('cancelId')
      if cancelId!='':
        message=receptionist.cancelAppointment(cancelId)
      else:
        message="Invalid input."
      return render_template('response.html',message=message)
  return render_template('receptionist.html',title='System Implementation Assignment - Receptionist Portal')

#Appointment Schedule Page
@app.route("/appointment_schedule",methods=["GET","POST"])
def appointment_schedule():
  #Fetch all records from the Appointments table and pass the results to the template
  cursor = mysql.connection.cursor()
  cursor.execute('SELECT appointment_id,patient_name,phone,appointment_time,type FROM Appointments JOIN Patients ON Appointments.patient_id=Patients.patient_id ORDER BY type DESC,appointment_time,patient_name')
  rows=cursor.fetchall()
  cursor.close()
  schedule=AppointmentSchedule(rows)
  if request.method == "POST":
    buttonAction=request.form.get('btn')
    #Add appointment
    if buttonAction=='Add Appointment':
      addPatientId=request.form.get('addPatientId')
      addAppointmentDate=request.form.get('addAppointmentDate')
      addAppointmentHour=request.form.get('addAppointmentHour')
      addAppointmentMinute=request.form.get('addAppointmentMinute')
      addAppointmentDatetime=addAppointmentDate+' '+addAppointmentHour+':'+addAppointmentMinute+':00'
      if addPatientId!='' and addAppointmentDate!='' and addAppointmentHour!='' and addAppointmentMinute!='':
        message=schedule.addAppointment(addPatientId,addAppointmentDatetime)
      else:
        message="Invalid input."
      return render_template('response.html',message=message)
    #Cancel appointment  
    elif buttonAction=='Cancel Appointment':
      cancelAppointmentId=request.form.get('cancelAppointmentId')
      if cancelAppointmentId!='':
        message=schedule.cancelAppointment(cancelAppointmentId)
      else:
        message="Invalid input."
      return render_template('response.html',message=message)
    elif buttonAction=='Find Next Available':
      message=schedule.findNextAvailable()
      return render_template('response.html',message=message)
  return render_template('appointment_schedule.html',title='System Implementation Assignment - Appointment Schedule',appointments=rows)
if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5000')