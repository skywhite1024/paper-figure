const sharp=require('sharp');const fs=require('fs');sharp(fs.readFileSync(process.argv[2]),{density:216}).png().toFile(process.argv[3]).catch(e=>{console.error(e);process.exit(1)});
