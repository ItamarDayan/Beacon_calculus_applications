
open System


     
    module UserInput=
        
        let printAndGet msg=
            printf "%A" msg
            let input = Console.ReadLine()
            input

        let getNumOfAgents=
            int( printAndGet "Enter number of agents")

        let getNumOfItems=
            int( printAndGet "Enter number of items")

        let getListOfInts numOfItems=
            let mutable list = []
            let mutable item = 0
            let mutable msg =""
            for i in [|1..numOfItems|] do
                 msg <- "Enter item #" + string(i)
                 item <- int( printAndGet msg)
                 list <- item::list
            list

        let getSortedIntList numOfItems=
            let list = getListOfInts numOfItems
            List.sort list 
                    
    module ExceptionsHandle =
        // define a "union" of two different alternatives
        type Result<'a, 'b> = 
            | Success of 'a  // 'a means generic type. The actual type
                             // will be determined when it is used.
            | Failure of 'b  // generic failure type

        // define all possible errors
        type FileErrorReason = 
            | FileNotFound of string
            | UnauthorizedAccess of string * System.Exception

    module FileHandle=  
        
        let openAndReadFile path =
            use reader = new System.IO.StreamReader(path:string) // Create a stream reader obj
            let file = reader.ReadToEnd()
            file
        
        let writeToFile (path:string) (fileName:string) (data:string) =
            use stream = new System.IO.StreamWriter(path + "/" + fileName)
            stream.Write(data)
           
        let getFolderPath =
            __SOURCE_DIRECTORY__

        let runFile fileName args = 
            let  procInfo = System.Diagnostics.ProcessStartInfo() 
            procInfo.Arguments <- args
            procInfo.FileName <- fileName
            procInfo.UseShellExecute <- false           
            System.Diagnostics.Process.Start(procInfo).WaitForExit()
            Threading.Thread.Sleep(100)
            
    module MathFunctions=
       
        let getPartialSums list = // # The method returns a list of the partial sums of a list

            let appendSumToList templist elem =
                let newElem = [((List.last templist) + elem)]
                templist @ newElem

            List.fold appendSumToList [0] list
 
    module PrintFunctions=
        
        module menu =
            
            let SSPMenu=
                let numOfItems = UserInput.getNumOfItems
                let numOfAgents = UserInput.getNumOfAgents
                let list = UserInput.getSortedIntList numOfItems
                (list, numOfAgents)


        let private addApos elem1 elem2 =
                match elem1 with
                |"" -> string(elem2)
                | _ -> elem1 + ", " + string(elem2)

        let printPartialSums list = 
            let partialSums = MathFunctions.getPartialSums list                                  
            List.fold addApos "" partialSums

        let printSetupParams len =
            let range = [1..len]
            List.fold (fun a b -> a + ", s" + string(b)) "s0" range

        let printStartAgents numOfAgents sum =
            let range = [0..numOfAgents-1]

            let printAgent partialString id=
                let str = "||P[0,0," + string(sum) + ",0," + string(id) + "]\n"
                partialString + str

            let str = List.fold printAgent ""  range
            str + ";"
         
        let printSetup len =
            let range = [1..len-1]
            List.fold (fun a b -> a + ".{s" + string(b) + "![1],fast}") "{s0![1],fast}" range

        let printBcsCode list numOfAgents = 
            let len = List.length list
            let sum = List.sum list
            
            let bcsCode = "
                fast = 1000;
                r = 1;


                Setup[" + printSetupParams len + "] = " + printSetup len + ".{start![1] ,fast};
                
                
                P[x,y,sum,last,serial] = {start?[1], r}.
                (
                [y==sum]->{done![x],fast} ||

                [y!=sum]->{y?[0..sum], fast}.({splitDown,1}.P[x,y+1,sum,0,serial] + {splitDiag,1}.P[x+1,y+1,sum,1,serial]) ||

                [y!=sum]->{~y?[0..sum],fast}.( [last == 0] -> {continueStraight, r}.P[x,y+1,sum,0,serial] + [last == 1]-> {continueStraight, r}.P[x+1,y+1,sum,1,serial])
                );


                Setup[" + printPartialSums list + "]" + "\n" + printStartAgents numOfAgents sum
            
            bcsCode
        
        let printResults results =
            for i in [|0..(Array.length results - 1)|] do
                let number = results.[i]
                printf "Agent on slot " 
                printf "%d" i
                printf  " : "
                printfn "%A" number
    
    module InterpretSimRes=
    
        type Split = {x:string ; y:string}
        type Agent = {x:string ; serial:string }

        type MixedType = 
          | S of Split
          | A of Agent
          | N


        // "deconstruction" of union type
        let isAgent x = 
          match x with
          | A {x=f; serial=l} -> 
                true
          | _ -> false 
         

        let parseLine (line:string) :MixedType = 
            
            let elements = line.Split("\t") |> Array.toList
            
            if(List.contains "done" elements) then
                let xIn = ( List.findIndex (fun x-> x = "x") elements) + 1
                let serialIn = ( List.findIndex (fun serial-> serial = "serial") elements) + 1

                A{x = elements.[xIn] ; serial = elements.[serialIn]}
               
            else
                if(List.contains "P" elements) then
                    let xIn = ( List.findIndex (fun x-> x = "x") elements) + 1
                    let yIn = ( List.findIndex (fun y-> y = "y") elements) + 1

                    S{x = elements.[xIn] ; y = elements.[yIn]}
                else
                N
        
        let interpretResults sum=
            let simulationOutput = FileHandle.openAndReadFile(FileHandle.getFolderPath + "/bin/Debug/netcoreapp3.1/simulationOutput")
    
            let lines = simulationOutput.Split("\n") |> Array.toList

            let parsedLines = List.map parseLine lines  // turn list of lines to list of MixedType (agent or split)
            
            let results = Array.zeroCreate (sum+1)

            for a in parsedLines do
                match a with
                | A{x=x ; serial = serial} 
                    -> results.[(int x)] <- results.[(int x)] + 1

                | _ -> printf ""
            
            results


open InterpretSimRes

[<EntryPoint>]
let main argv =
    
    let (list, numOfAgents) = PrintFunctions.menu.SSPMenu  // show SSP menu and get inputs
    let sum = List.sum list                                // get sum of list

    let bcsCode =  PrintFunctions.printBcsCode list numOfAgents // create bcs code text
    
    FileHandle.writeToFile FileHandle.getFolderPath "bcs_generated_code.bc" bcsCode // create bcs txt file
    
    let bcsCodePath = FileHandle.getFolderPath + "/bcs_generated_code.bc"
    let bcsExecPath = "/home/id/bcs/bin/bcs"

    FileHandle.runFile bcsExecPath bcsCodePath      // run bcs.exe on our bcs code

    let results = interpretResults sum              // interpret simulation output
    PrintFunctions.printResults results             // print the results
    
    0 // return an integer exit code



