//Used for debugging
function displayForms(){
  //displays Enlglish forms all the way to 2007
  for(i = 0; i <  document.getElementsByName("documentation_button").length; i += 2){
    console.log(document.getElementsByName("documentation_button")[i])
  }
}

function changeInputs(year){

  data_inputs = document.getElementsByName("data")
  year_inputs = document.getElementsByName("year")

  for(i = 0; i < data_inputs.length; i++){
      data_inputs[i].value = year
  }
  for(i = 0; i < year_inputs.length; i++){
      year_inputs[i].value = year
  }

}

function submit(n=0){
  //multiplying n by 2 gets every second form; i.e. only the English forms
  document.getElementsByName("documentation_button")[n*2].submit()
}

changeInputs(2017)
//displayForms()
submit()
