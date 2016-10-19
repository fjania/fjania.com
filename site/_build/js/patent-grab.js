var patents = [];

function fetch(){
  jQuery('search-result-item').each(
    function(i,e){
      var title = $(e).find('.result-title #htmlContent').text();
      var datestr = $(e).find('.abstract .dates').text();
      var dateList = datestr.replace(/ • /g, ',').split(',');
      var dates = {};
      dateList.forEach(function(e){
        var t = e.split(' ')[0]
        var d = e.split(' ')[1]
        dates[t] = d;
      })

      var abstract = $(e).find('.abstract > div > raw-html #htmlContent').text();
      patents.push({
        title: title,
        dates: dates,
        abstract: abstract
      })
    }
  );
}
