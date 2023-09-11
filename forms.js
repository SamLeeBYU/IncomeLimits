window.changeInputs = function(year){

  //TODO
  /*

  */

  forms = document.getElementsByName("documentation_button")
  trueSubmission = '<input type="HIDDEN" name="trueSubmission" value="yes">'

  for(i = 0; i < forms.length; i += 2){ //iterate over every one because we only want the English forms
    form = forms[i]
    //When we change the action of the form we change all the HTML forms on the page to POST to the year that we are iterating through in our python program
    //You can see what year the program is iterating through by
    //    1) Looking at what the Selenium Webdriver is doing in real time
    //    2) Looking at the diagnostic information I'm having our python program output to the console

    //Changing this makes it seem like a real request was sent to the server (because, in a sense, it was)
    form.action = `/portal/datasets/il/il${year}/select_Geography.odn`
    if([2015, 2014].includes(year)){
      //This bit of html is needed for the form for years 2014-2015
      form.innerHTML += trueSubmission
    }

    if([2007, 2008, 2009].includes(year)){
      //use this form action url instead
      //we'll have to go through a different selenium process to get the data (as mapped out in main.py),
      //but we can still get the data nonetheless
      form.action = `https://www.huduser.gov/portal/datasets/il/il${year}/select_Geography.odb`
    }
  }

  //Change all the hidden inputs

  data_inputs = document.getElementsByName("data")
  year_inputs = document.getElementsByName("year")

  for(i = 0; i < data_inputs.length; i++){
      data_inputs[i].value = year
  }
  for(i = 0; i < year_inputs.length; i++){
      year_inputs[i].value = year
  }

}

//we can choose what form we want to submit (n) regardless of the url
window.submit = function(year){
  //multiplying n by 2 gets every second form; i.e. only the English forms
  //document.getElementsByName("documentation_button")[((new Date().getFullYear() - year))*2].submit()
  
  //document.getElementsByName("documentation_button")[0].submit()
  document.querySelector("form[name='documentation_button']").submit()
}