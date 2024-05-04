//selecting all required elements
const start_btn = document.querySelector(".start_btn button");
const info_box = document.querySelector(".info_box");
const exit_btn = info_box.querySelector(".buttons .quit");
const continue_btn = info_box.querySelector(".buttons .restart");
const quiz_box = document.querySelector(".quiz_box");
const result_box = document.querySelector(".result_box");
const option_list = document.querySelector(".option_list");
const time_line = document.querySelector("header .time_line");
const timeText = document.querySelector(".timer .time_left_txt");
const timeCount = document.querySelector(".timer .timer_sec");
const waitTxt = document.querySelector(".result_box .wait_text");
const camOpen = document.querySelector(".camera")


// if startQuiz button clicked
start_btn.onclick = () => {
    info_box.classList.add("activeInfo"); //show info box
    camOpen;
};

// if exit quiz button clicked
exit_btn.onclick = () => {
    location.replace("./quiz.html");
};

// if continue quiz button clicked
continue_btn.onclick = () => {
    info_box.classList.remove("activeInfo"); //hide info box
    quiz_box.classList.add("activeQuiz") //show quiz
    showQuetions(0);
    queCounter(1);
    startTimer(15);
    startTimerLine(0);
    // cameraStart();
}

function showQuetions(index){
    const que_text = document.querySelector(".que_text");

    // creating a new span and div tag for questions and option and passing the value using array
    let que_tag = 
        "<span>" +
        questions[index].numb + ". " + 
        questions[index].question +
        "</span>";

    let option_tag = 
        '<div class="option"><span>' +
        questions[index].options[0] + 
        "</span></div>" +
        '<div class="option"><span>' +
        questions[index].options[1] + 
        "</span></div>" +
        '<div class="option"><span>' +
        questions[index].options[2] + 
        "</span></div>" +
        '<div class="option"><span>' +
        questions[index].options[3] + 
        "</span></div>" ;

    que_text.innerHTML = que_tag; //adding new span tag inside que_tag
    option_list.innerHTML = option_tag; //adding new div tag inside option_tag

    const option = option_list.querySelectorAll(".option");

    //set on-click attribute to all available options
    for (i=0; i<option.length; i++){
        option[i].setAttribute("onclick", "optionSelected(this)");
    }
}

let counter;
let counterLine;
let que_count = 0;
let que_numb = 1;
let userScore = 0;
let timeValue = 15;
let widthValue = 0;

let tickIconTag = '<div class="icon tick"><i class="fas fa-check"></i></div>';
let crossIconTag = '<div class="icon cross"><i class="fas fa-times"></i></div>';

function optionSelected(answer){
    clearInterval(counter); //clear counter
    clearInterval(counterLine); //clear counterLine
    let userAns = answer.textContent; //getting user selected option
    let correcAns = questions[que_count].answer; //getting correct answer
    const allOptions = option_list.children.length; //getting all options items

    if (userAns == correcAns){
        userScore += 1; //incrementing the user's score
        answer.classList.add("correct"); //adding green color to correct selected option
        answer.insertAdjacentHTML("beforeend", tickIconTag); //adding tick icon to correct selected option
        console.log("Correct Answer");
        console.log("Your correct answer = "+ userScore);
    }
    else{
        answer.classList.add("incorrect"); //adding red color to incorrect selected option
        answer.insertAdjacentHTML("beforeend", crossIconTag); //adding cross icon to incorrect selected option
        console.log("Wrong Answer");

        for (i=0; i<allOptions; i++){
            if(option_list.children[i].textContent == correcAns){
                //if there is an option which is matched to an array answer
                option_list.children[i].setAttribute("class", "option correct"); //adding green color to matched option
                option_list.children[i].insertAdjacentHTML("beforeend", tickIconTag); //adding tick icon to matched option
                console.log("Auto Selected correct answer.");
            }
        }
    }
    for(i=0; i<allOptions; i++){
        option_list.children[i].classList.add("disabled"); //once user select an option then disabled all options
    }
    next_btn.classList.add("show"); //show the next button if user selected any option
}

const next_btn = document.querySelector("footer .next_btn");
const bottom_ques_counter = document.querySelector("footer .total_que");

// if next ques button clicked
next_btn.onclick = () => {
    if(que_count < questions.length-1){
        //if question count is less than total questions
        que_count++;
        que_numb++;
        showQuetions(que_count);
        queCounter(que_numb);
        clearInterval(counter);
        clearInterval(counterLine);
        startTimer(timeValue);
        startTimerLine(widthValue);
        timeText.textContent = 'Time Left';
        next_btn.classList.remove("show");
    }
    else{
        clearInterval(counter);
        clearInterval(counterLine);
        showResult();
    }
};

function queCounter(index){
    //creating a new span tag and passing the question number and total questions
    let totalQueCounTag = 
        "<span><p>"+
        index +
        "</p> of <p>"+
        questions.length +
        "</p> Questions</span>"
    bottom_ques_counter.innerHTML = totalQueCounTag;
}

function startTimer(time){
    counter = setInterval(timer, 1000);
    function timer() {
        timeCount.textContent = time; //changing the value of timeCount with time value
        time--; //decrement the time value

        if(time<9){
            //if timer is less than 9
            let addZero = timeCount.textContent;
            timeCount.textContent = "0" + addZero; //add a 0 before the time value
        }

        if (time<0){
            //if timer is less than 0
            clearInterval(counter);
            timeText.textContent = "Time Off"; //change the time text to timeOff
            const allOptions = option_list.children.length;
            let correcAns = questions[que_count].answer;
            for (i=0; i<allOptions; i++){
                if(option_list.children[i].textContent == correcAns){
                    option_list.children[i].setAttribute("class", "option correct");
                    option_list.children[i].insertAdjacentHTML("beforeend", tickIconTag);
                    console.log("Time Off: Auto selected correct answer.");
                }
            }
            for(i=0; i<allOptions; i++){
                option_list.children[i].classList.add("disabled");
            }
            next_btn.classList.add("show");
        }
    }
}

function startTimerLine(time){
    counterLine = setInterval(timer, 29);
    function timer(){
        time += 1;
        time_line.style.width = time+"px";
        if(time > 549){
            clearInterval(counterLine);
        }
    }
}

function showResult(){
    info_box.classList.remove("activeInfo"); //hide info box
    quiz_box.classList.remove("activeQuiz"); //hide quiz box
    result_box.classList.add("activeResult"); //show result box
    const scoreText = result_box.querySelector(".score_text");

    if (userScore > 3){
        let scoreTag =  
            "<span>Congrats! You got <p>" + userScore +
            "</p> out of <p>"+ questions.length +
            "</p></span>";
        scoreText.innerHTML = scoreTag;
    }
    else{
        let scoreTag = 
            "<span>Nice, You got <p>"+ userScore+
            "</p> out of <p>"+
            questions.length +
            "</p></span>";
        scoreText.innerHTML = scoreTag;
    }
    // Wait for 10 seconds (10000 milliseconds) and then redirect to google.com
    setTimeout(function() {
        window.location.href = 'http://127.0.0.1:5000';
    }, 10000);
}

// Disable screenshot
window.addEventListener('screenshotTaken', function(e) {
    e.preventDefault();
});

// Disable screen recording
window.addEventListener('beforeunload', function(e) {
    var mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = function(e) {
        // Handle data
    };
    mediaRecorder.onstop = function() {
        // Handle recording stop
    };
    mediaRecorder.stop();
});
