//>>built
require({cache:{"JBrowse/Plugin":function(){define("JBrowse/Plugin",["dojo/_base/declare","JBrowse/Component"],function(d,f){return d(f,{constructor:function(a){this.name=a.name;this.cssLoaded=a.cssLoaded;this._finalizeConfig(a.config)},_defaultConfig:function(){return{baseUrl:"/plugins/"+this.name}}})})}}});
define("HideTrackLabels/main","dojo/_base/declare,dojo/_base/lang,dojo/Deferred,dojo/dom-construct,dijit/form/Button,dojo/fx,dojo/dom,dojo/dom-style,dojo/on,dojo/query,dojo/dom-geometry,JBrowse/Plugin".split(","),function(d,f,a,k,g,h,b,l,m,i,e,j){return d(j,{constructor:function(){this._defaultConfig();var a=this;this.browser.afterMilestone("initView",function(){var b=dojo.byId("navbox");a.browser.hideTitlesButton=new g({title:"Hide/Show Track Titles",id:"hidetitles-btn",width:"24px",onClick:dojo.hitch(a,
function(b){a.browser.showTrackLabels("toggle");dojo.stopEvent(b)})},dojo.create("button",{},b))});this.browser.showTrackLabels=function(a){if(null!=dojo.byId("hidetitles-btn")){var c=1;"show"==a&&(dojo.removeAttr(b.byId("hidetitles-btn"),"hidden-titles"),c=1);"hide"==a&&(dojo.attr(b.byId("hidetitles-btn"),"hidden-titles",""),c=-1);if("hide-if"==a)if(dojo.hasAttr(b.byId("hidetitles-btn"),"hidden-titles"))c=-1;else return;"toggle"==a&&(dojo.hasAttr(b.byId("hidetitles-btn"),"hidden-titles")?(dojo.removeAttr(b.byId("hidetitles-btn"),
"hidden-titles"),c=1):(dojo.attr(b.byId("hidetitles-btn"),"hidden-titles",""),c=-1));dojo.attr(b.byId("hidetitles-btn"),"disabled","");setTimeout(function(){dojo.removeAttr(b.byId("hidetitles-btn"),"disabled")},1E3);i(".track-label").forEach(function(a){var b=e.getMarginBox(a).w;h.slideTo({node:a,top:e.getMarginBox(a).t.toString(),left:(e.getMarginBox(a).l+b*c).toString(),unit:"px"}).play()})}};dojo.subscribe("/jbrowse/v1/n/tracks/redraw",function(){a.browser.showTrackLabels("hide-if")})}})});