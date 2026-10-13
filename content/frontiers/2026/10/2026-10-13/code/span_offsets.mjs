// Consumes Python code-point offsets against the identical, unnormalised text.
import fs from 'node:fs';
function checkedSlice(text,start,end){
 const points=Array.from(text);
 if(!Number.isInteger(start)||!Number.isInteger(end)||start<0||end<start||end>points.length)throw new RangeError('Invalid code-point interval');
 const start16=points.slice(0,start).join('').length;
 const end16=points.slice(0,end).join('').length;
 return {correct:points.slice(start,end).join(''),viaUtf16Map:text.slice(start16,end16),start16,end16};
}
const rows=JSON.parse(fs.readFileSync(new URL('./span-inputs.json',import.meta.url),'utf8')).map(x=>{
 const result=checkedSlice(x.text,x.start,x.end);
 if(result.correct!==x.expected||result.viaUtf16Map!==x.expected)throw new Error('Offset mismatch');
 return {...x,...result,naive:x.text.slice(x.start,x.end),utf16Units:x.text.length};
});
let invalidRejected=false;try{checkedSlice('🙂',0,2);}catch(e){invalidRejected=e instanceof RangeError;}
if(!invalidRejected)throw new Error('Invalid range accepted');
const report={note:'Synthetic local protocol demonstration; not Vela model evaluation',node:process.version,cases:rows,invalidRejected};
fs.writeFileSync(new URL('./span-results.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
