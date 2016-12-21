set output 'TESTCIFAR64.png'
set title 'TESTCIFAR64'
set term png size 1920,1080
set datafile missing '#'
set style data lines
set key off
set xlabel 'Time (Seconds)'
set ylabel 'Power (Watts)'
set yrange [-0.01:10.347050000000001]
set xrange [0:22.619859969619874]
file = 'temp.dat
cols = int(system('head -1 '.file.' | wc -w'))
plot for [i=2:cols] 'temp.dat' using 1:i title columnheader(i+1)
