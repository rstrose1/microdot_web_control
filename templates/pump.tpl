<!DOCTYPE html>
<html>
<style>
.aligncenter {
    text-align: center;
}
a {
    font-size: 150px; /* example size, can be any size, in px, em, rem, % */
}

</style>

<head>
<title>Pump Pressure</title>
</head>

<body>

    <script>function timedRefresh(timeoutPeriod){
        setTimeout("location.reload(true);", timeoutPeriod);
    }
    window.onload = timedRefresh(2000)

    </script>

<h1 style="text-align:center"> Pump Pressure </h1>

<p class="aligncenter">
<progress max="100" value={{ pump_info_str }}></progress>

<h1> Pump Status </h1>
<div class='container'>
<h2>{{ content }}</h2>
</div>

</p>
</body>
</html>
