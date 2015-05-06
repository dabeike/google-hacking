/** the function can reg the following type：
 ** <cite class="_Rm">www.speedtest.net/</cite>
 ** <cite class="_Rm bc">www.speedtest.net/</cite>
 ** <cite class="_Rm">www.<b>gov</b>.cn/zhuanti/2015lh/premierreport/</cite>
 ** usage: copy this to chrome-console, it will anaylysis your google result,and give a useful text like:
 ** 	site:www.jiangsu.gov.cn OR site:www.jshrss.gov.cn OR site:www.jshb.gov.cn OR site:www.jsjyt.gov.cn OR site:www.jsagri.gov.cn OR site:big OR site:big OR site:www.fhzbmfw.gov.cn OR site:www.jstd.gov.cn OR site:rd.sqsc.gov.cn 
 ** 	so you can google again with the giving keywords
 ** 实际利用：例如需要查看某个省市的政府部门是否被挂上博彩信息，先搜索 南京 site:gov.cn,在console里输入本脚本
 ** 	再打开一个新页面，google  博彩 site:www.jiangsu.gov.cn OR site:www.jshrss.gov.cn ..
 **/
function GetKeyWords(){
	var html=document.body.innerHTML
	/*去掉字体加粗<b></b>*/
	html=html.replace(/<b>|<\/b>/g, "")
	var reg=new RegExp('<cite class="_Rm( bc)?">(http:\/\/)?([a-zA-Z.-]*)(\/?.*?)<\/cite>',"g")
	var match_temp='';
	var match_res='';
	var count=0;
	while((match_temp=reg.exec(html)) != null){
		match_res+=' OR site:'+match_temp[3];
		count++;
	}
	console.log('共统计'+count+'个URL,google搜索关键词：'+match_res.substring(4))
}

GetKeyWords();