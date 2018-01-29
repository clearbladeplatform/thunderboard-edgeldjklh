function add(a, b){
  return a + b;
}
 
function numericSort(a,b) {
    return a - b;
}
 
function numSquare(a) {
  return Math.pow(a, 2);
}
 
function randomArrayThousand(numElems) {
    var arr = [];
    for (var i=0; i<numElems; i++){
        arr.push(Math.round(Math.random() * 1000) + 1);
    }
    return arr;
}
 
function median(arr) {
    arr.sort(numericSort);
    if (arr.length % 2 === 0){
      return arr[arr.length/2];
    }
    else{
      return (arr[Math.floor(arr.length/2 - 1)] + arr[Math.floor(arr.length/2)]) / 2;
    }
}
 
function average(arr){
    var sum = arr.reduce(add);
    return sum / arr.length;
}
 
function deviations(arr, mean){
    return arr.map(function(a, mean) { return a - mean});
}
 
function squaredDeviations(arr){
    return arr.map(numSquare);
    // return arr.map(function(a){ return Math.pow(a, 2)});
}
 
function variance(arr){
 
    var avg = average(arr);
    return squaredDeviations(deviations(arr, avg)).reduce(add) /  arr.length;
}
 
function stdDev(arr, sample){
    // default value of sample is false. If sample is defined then we apply Bessel's Correction.
    sample = typeof sample !== 'undefined' ? sample : false;
    return sample ? Math.sqrt(variance(arr)) - 1 : Math.sqrt(variance(arr));
}
 
function zScore(x, m, std){
    return Math.abs(x - m) / std;
}
 
function getZPercent(z)
{
    // http://stackoverflow.com/questions/16194730/seeking-a-statistical-javascript-function-to-return-p-value-from-a-z-score
    //z == number of standard deviations from the mean
 
    //if z is greater than 6.5 standard deviations from the mean
    //the number of significant digits will be outside of a reasonable
    //range
    if ( z < -6.5)
        return 0.0;
    if( z > 6.5)
        return 1.0;
 
    var factK = 1;
    var sum = 0;
    var term = 1;
    var k = 0;
    var loopStop = Math.exp(-23);
    while(Math.abs(term) > loopStop)
    {
        term = 0.3989422804 * Math.pow(-1,k) * Math.pow(z,k) / (2 * k + 1) / Math.pow(2,k) * Math.pow(z,k+1) / factK;
        sum += term;
        k++;
        factK *= k;
    }
    sum += 0.5;
 
    return sum;
}