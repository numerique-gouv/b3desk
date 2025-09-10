const seconds_before_refresh = 10;
let joinMeeting = () => {
    document.getElementById("joinMeetingForm").submit()
}
setTimeout(joinMeeting, seconds_before_refresh * 1000)
