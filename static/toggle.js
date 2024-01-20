var filter = {"msg_type":"send-msg", "to":"send-all"}
var chatHistory = document.getElementById("chat-history");
var currentUsers = [];

function toggleVideo(){
    var videoButton = document.getElementById("video-button");
    var userVideo = document.getElementById("user-video");
    console.log(videoButton.getAttribute('src'))
    fetch("http://127.0.0.1:5000/clients", {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        }, 
        body: JSON.stringify({"action":"videoButton"})}
    ).then((res)=>{
        return res.json();
    }).then((data)=>{
        console.log(data);
        videoButton.setAttribute('src', data.video_button)
        userVideo.setAttribute('src', data.user_video)
    }).catch(error => console.error('Error:', error));
}



var multipleVideo = document.getElementById("multiple-video");
setInterval(()=>{
    fetch("http://127.0.0.1:5000/clients", {
        method:'POST',
        headers: {
            'Content-Type': 'application/json',
        }, 
        body: JSON.stringify({"action":"clients"})
    }).then((res)=>res.json()
    ).then((data)=>{
        var users = [...data.users];
        console.log("users: "+users);
        if(users){
            try{
                users.forEach((x)=>{
                    if(!currentUsers.includes(x)){
                        // currentUsers.push(x)
                        
                        let newDiv = document.createElement("div");
                        newDiv.id = x;
                        newDiv.className = "small-video";
                        newDiv.onclick = function(event){
                            
                            console.log("Id: ", this.id)
                            let clicked_img = document.querySelector("#" + this.id + " img");
                            // if(this.id == "user-video"){
                            //     clicked_img = document.querySelector("#user-video");
                            // }else{
                            //     clicked_img = 
                            // }
                            let largeVideo = document.getElementById("user-video");
                        
                            let src1 = largeVideo.getAttribute("src");
                            let src2 = clicked_img.getAttribute("src");
                            
                            let img1 = document.createElement("img");
                            img1.src = src1;
                         
                            let img2 = document.createElement("img");
                            img2.src = src2;
                            img2.id = "user-video"
                            

                            let mainVideo = document.getElementById("main-video");
                            // let multipleVideo = document.getElementById("multiple-video");

                            largeVideo.remove();
                            mainVideo.appendChild(img2);
                            clicked_img.remove();
                            document.getElementById(this.id).appendChild(img1);

                        }

                        
                        let newImg = document.createElement("img");
                        newImg.src = "/video_feed/" + x;

                        newDiv.appendChild(newImg);
                        console.log("New Div: ", newDiv);
                        multipleVideo.appendChild(newDiv);
                    }
                })
                
                // console.log("currentUsers: ", typeof(currentUsers), currentUsers, "NewSet: ", typeof(users), users);
                currentUsers.forEach((x)=>{
                    if(!users.includes(x)){
                        document.getElementById(x).remove();
                    }
                });
                console.log("before update current users: ", currentUsers)
                currentUsers = users;
                console.log("current Users: ", currentUsers)



                // APPENDING THE REPLIES TO THE CHAT
                let replies = [...data.messages]
                replies.forEach(reply=>{
                    let newDiv = document.createElement("div");
                    newDiv.className = "msg-box";

                    let formUser = document.createElement("p");
                    formUser.className = "from-username";
                    formUser.innerText = reply.username;

                    let newPara = document.createElement("p");
                    newPara.className = "message";
                    newPara.innerText = reply.msg;

                    newDiv.appendChild(formUser);
                    newDiv.appendChild(newPara);

                    chatHistory.appendChild(newDiv);
                });
            }catch(e){
                console.log("Exception catched: "+ e);
            }
        }
        
        
    })
}, 5000)

function toggleAudio(){
    var audioButton  = document.getElementById("audio-button");
    fetch("http://127.0.0.1:5000/clients", {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        }, 
        body: JSON.stringify({"action":"audioButton"})}
    ).then(res=>res.json()
    ).then((data)=>{
        console.log(data);
        audioButton.setAttribute('src', data.audio_button)
    }).catch(error => console.error('Error:', error));
}

function toggleSpeaker(){
    var speakerButton  = document.getElementById("speaker-button");
    fetch("http://127.0.0.1:5000/clients", {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        }, 
        body: JSON.stringify({"action":"speakerButton"})}
    ).then(res=>res.json()
    ).then((data)=>{
        console.log(data);
        speakerButton.setAttribute('src', data.speaker_button)
    }).catch(error => console.error('Error:', error));
}

function showOptions(){
    let options = document.querySelector("#chat-options .filters");
    options.classList.toggle("display");
}

function getMsgFilters(){
    showOptions();
    let selectUsers = document.querySelector("#chat-options .select-users");
    if(document.getElementById("send-msg").checked){
        filter.msg_type = "send-msg";
    }else if(document.getElementById("send-file").checked){
        filter.msg_type = "send-file"
    }
    if(document.getElementById("send-all").checked){
        filter.to = "send-all";
        if(!selectUsers.classList.contains("display")){
            selectUsers.classList.toggle("display")
        }
    }else if(document.getElementById("send-usernames").checked){
        filter.to = "send-usernames";
        if(selectUsers.classList.contains("display")){
            selectUsers.classList.toggle("display")
        }
    }
}



function getUsernames(){
    let userNamesList = document.getElementById("usernames-list");

    if(userNamesList.classList.contains("display")){
        userNamesList.innerHTML = "";
        currentUsers.forEach(name=>{
            userNamesList.innerHTML += '<input type="checkbox" name="usernames" value="'+name+'"> <label >'+name+'</label><br>'
        });
        userNamesList.classList.toggle("display");
    }else{
        userNamesList.classList.toggle("display");
    }
}


function sendMessage(){
    let txt = document.querySelector('.chat-input .input-box');
    let msg = txt.value;

    let newDiv = document.createElement("div");
    newDiv.className = "msg-box user-msg";

    let newPara = document.createElement("p");
    newPara.className = "message";
    newPara.innerText = msg;
    txt.value = "";

    newDiv.appendChild(newPara);
    chatHistory.appendChild(newDiv);

    let checkedBoxes = [...document.querySelectorAll('input[name=usernames]:checked')];
    let selectedUsers = [...checkedBoxes.map(box=> box.value)];
    console.log("Selected Users: ", selectedUsers);

    fetch("http://127.0.0.1:5000/msgs", {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        }, 
        body: JSON.stringify({...filter, ...{"msg":msg, "selected_users": selectedUsers}})}
    ).then((res)=>res
    ).then(data=>data
    ).catch(error => console.log('Error:', error));

}

