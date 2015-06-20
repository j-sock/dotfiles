false_hour=$(($(clock -f '%H') + 4))

echo $false_hour:$(clock -f '%M')