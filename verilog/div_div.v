module div_div
  (
    input wire clk,
    input wire rst,
    input wire div_ready,
    input wire div_accept,
    output reg div_valid,
    input wire signed [127:0] div_in_a,
    input wire signed [63:0] div_in_b,
    output reg signed [127:0] div_out_0
  );

  //localparams
  localparam div_b1_INIT = 0;
  localparam div_b1_S0 = 1;
  localparam div_b1_FINISH = 2;
  
  //signals: 
  reg        [1:0] div_state;
  reg signed [127:0] a;
  reg signed [63:0] b;
  
  always @(posedge clk) begin
    if (rst) begin
      a <= 0;
      b <= 0;
      div_out_0 <= 0;
      div_state <= div_b1_INIT;
    end else begin //if (rst)
      case(div_state)
      div_b1_INIT: begin
        div_valid <= 0;
        if (div_ready == 1) begin
          a <= div_in_a;          /* div.py [3]: def div(a: int128, b: int64) -> int128: */
          b <= div_in_b;          /* div.py [3]: def div(a: int128, b: int64) -> int128: */
          div_state <= div_b1_FINISH;
        end
        if (!div_ready) begin
          a <= 0;
          b <= 0;
          div_out_0 <= 0;
        end
      end
      div_b1_FINISH: begin
        div_valid <= 1;
        if (div_accept == 1) begin
          div_state <= div_b1_INIT;
        end
        div_out_0 <= (a / b);        /* div.py [4]: return a // b */
      end
      endcase
    end
  end
  

endmodule

