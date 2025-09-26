secondsBeforeRefresh = document.getElementById("seconds_before_refresh").value
let joinMeeting = () => {
    document.getElementById("joinMeetingForm").submit()
}
setTimeout(joinMeeting, secondsBeforeRefresh * 1000)
